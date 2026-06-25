"""Detective agent. Resolves GREY ZONE skills to binary MATCH / NO MATCH.

Called by the pipeline only when the Linguist flags at least one skill as GREY ZONE
(cosine similarity 0.60-0.85).  For each ambiguous skill the agent asks the LLM:
  "Is there explicit evidence for this skill in the raw CV text?"
and returns a binary verdict.  After Detective runs, Podium receives a fully resolved
skill list with zero GREY ZONE entries.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

import ollama
from pydantic import BaseModel, ValidationError

from src.config import (
    MAX_RETRIES, RETRY_DELAY,
    DETECTIVE_MAX_WORKERS  as MAX_WORKERS,
    DETECTIVE_OLLAMA_TIMEOUT as OLLAMA_TIMEOUT,
    DETECTIVE_CONTEXT_WINDOW as CONTEXT_WINDOW,
)


# Module-level client with a real per-request timeout. The underlying httpx
# client used by `ollama.Client` enforces this on every HTTP call, so a stuck
# Ollama generation aborts at OLLAMA_TIMEOUT seconds instead of hanging the
# whole future. Thread-safe — shared across the Detective worker pool.
_CLIENT = ollama.Client(timeout=OLLAMA_TIMEOUT)


class DetectiveVerdict(BaseModel):
    classification: Literal["MATCH", "NO MATCH"]  # binary — never GREY ZONE
    evidence: str    # exact quote from CV, or "No evidence found"
    reasoning: str   # one sentence


class DetectiveResult(BaseModel):
    verdicts: dict[str, DetectiveVerdict]  # keyed by vacancy skill name
    summary: dict                           # {"resolved_to_match": int, "resolved_to_no_match": int}


_SYSTEM_PROMPT = """\
You are a CV analyst. Given one job skill and a full CV text, determine if the \
candidate has that skill based on EXPLICIT evidence in the CV.
Return ONLY valid JSON: {"classification": "MATCH"|"NO MATCH", "evidence": "...", "reasoning": "..."}
Rules:
- MATCH only if the skill is explicitly demonstrated (projects, roles, tools listed).
- NO MATCH if there is no clear evidence, even if related skills are present.
- Quote the exact CV text as evidence. Never infer or assume.\
"""


def _relevant_context(skill: str, raw_text: str, extra_terms: list[str] | None = None) -> str:
    """Return a focused excerpt of raw_text centred on the best keyword hit.

    Searches for the skill name first, then any extra_terms (e.g. the Linguist's
    best_match candidate skill). Takes the first hit found. Falls back to the
    first 1500 chars if nothing matches — useful when the skill truly isn't there.
    """
    for term in [skill] + (extra_terms or []):
        idx = raw_text.lower().find(term.lower())
        if idx != -1:
            start = max(0, idx - CONTEXT_WINDOW)
            end   = min(len(raw_text), idx + CONTEXT_WINDOW)
            return raw_text[start:end]
    return raw_text[:1500]


def _resolve_one(
    skill: str,
    raw_text: str,
    model: str,
    best_match: str | None = None,
) -> DetectiveVerdict:
    """One Ollama call (with retries) for a single grey-zone skill."""
    context   = _relevant_context(skill, raw_text, [best_match] if best_match else None)
    user_msg  = f'Skill to evaluate: "{skill}"\n\nCV text:\n{context}'
    sys_chars   = len(_SYSTEM_PROMPT)
    user_chars  = len(user_msg)
    ctx_chars   = len(context)
    print(
        f"[detective.debug] PROMPT skill='{skill}' sys={sys_chars}c user={user_chars}c "
        f"context={ctx_chars}c total≈{sys_chars+user_chars}c (~{(sys_chars+user_chars)//4} tok)",
        flush=True,
    )
    last_exc: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        t_call = time.time()
        try:
            response = _CLIENT.chat(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                format="json",
                options={"temperature": 0},
            )
            content = response["message"]["content"].strip()
            raw_preview = content.replace("\n", " ")[:200]
            print(
                f"[detective.debug] RAW skill='{skill}' attempt={attempt} len={len(content)} "
                f"content='{raw_preview}'",
                flush=True,
            )
            data = json.loads(content)
            verdict = DetectiveVerdict.model_validate(data)
            if verdict.classification == "NO MATCH":
                ev = (verdict.evidence or "").replace("\n", " ")[:140]
                rs = (verdict.reasoning or "").replace("\n", " ")[:140]
                print(
                    f"[detective.debug] NO_MATCH skill='{skill}' evidence='{ev}' reasoning='{rs}'",
                    flush=True,
                )
            return verdict

        except (json.JSONDecodeError, ValidationError) as e:
            last_exc = e
            print(
                f"[detective.debug] PARSE_ERR skill='{skill}' attempt={attempt} "
                f"type={type(e).__name__} msg='{str(e)[:140]}'",
                flush=True,
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** (attempt - 1)))

        except Exception as e:
            last_exc = e
            elapsed = time.time() - t_call
            # Distinguish HTTP/read timeouts (httpx.ReadTimeout, TimeoutException, ...)
            # from generic connection errors — they call for different retry policies.
            type_name = type(e).__name__
            is_timeout = "Timeout" in type_name or elapsed >= OLLAMA_TIMEOUT * 0.9
            tag = "TIMEOUT" if is_timeout else "CONN_ERR"
            print(
                f"[detective.debug] {tag} skill='{skill}' attempt={attempt} "
                f"elapsed={elapsed:.1f}s type={type_name} msg='{str(e)[:140]}'",
                flush=True,
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** attempt))

    print(
        f"[detective.debug] FALLBACK skill='{skill}' last_exc={type(last_exc).__name__ if last_exc else None}: "
        f"'{str(last_exc)[:200] if last_exc else ''}'",
        flush=True,
    )
    return DetectiveVerdict(
        classification="NO MATCH",
        evidence="Parse failed after retries",
        reasoning=str(last_exc),
    )


def resolve(
    grey_zone_skills: list[str],
    raw_text: str,
    model: str = "llama3",
    aliases: dict[str, str] | None = None,
) -> DetectiveResult:
    """Resolve each grey-zone skill to MATCH or NO MATCH.

    Args:
        grey_zone_skills: skill names flagged as GREY ZONE by the Linguist
        raw_text:         full extracted CV text (from CandidateProfile.raw_text)
        model:            Ollama model name
        aliases:          optional mapping skill → best_match from the Linguist;
                          used to find the relevant CV section when the skill name
                          itself does not appear verbatim in the text
    """
    """Resolve each grey-zone skill to MATCH or NO MATCH.

    Args:
        grey_zone_skills: skill names flagged as GREY ZONE by the Linguist
        raw_text:         full extracted CV text (from CandidateProfile.raw_text)
        model:            Ollama model name

    Returns:
        DetectiveResult with one verdict per skill and a summary count.
    """
    _aliases = aliases or {}
    verdicts: dict[str, DetectiveVerdict] = {}
    total = len(grey_zone_skills)
    workers = min(MAX_WORKERS, total) if total > 0 else 1
    print(f"[detective] launching {total} grey-zone resolutions with {workers} workers", flush=True)
    t_start = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(_resolve_one, skill, raw_text, model, _aliases.get(skill)): skill
            for skill in grey_zone_skills
        }
        for future in as_completed(futures):
            skill = futures[future]
            # No timeout on future.result(): the real per-request timeout is
            # enforced by the ollama Client (httpx). When that fires, _resolve_one
            # handles the exception and the future returns normally with a
            # NO MATCH fallback — never raises here.
            verdicts[skill] = future.result()
            done += 1
            print(
                f"[detective]   [{done}/{total}] '{skill}' → {verdicts[skill].classification} "
                f"(elapsed={time.time()-t_start:.1f}s)",
                flush=True,
            )

    resolved_match    = sum(1 for v in verdicts.values() if v.classification == "MATCH")
    resolved_no_match = sum(1 for v in verdicts.values() if v.classification == "NO MATCH")

    return DetectiveResult(
        verdicts=verdicts,
        summary={
            "resolved_to_match":    resolved_match,
            "resolved_to_no_match": resolved_no_match,
        },
    )
