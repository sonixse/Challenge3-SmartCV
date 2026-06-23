"""Detective agent — resolves GREY ZONE skills to binary MATCH / NO MATCH.

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

MAX_RETRIES    = 3
RETRY_DELAY    = 2.0   # seconds (doubles on each retry)
MAX_WORKERS    = 3     # concurrent Ollama calls (one per grey-zone skill)
CONTEXT_WINDOW = 400   # chars around keyword match sent to the LLM
OLLAMA_TIMEOUT = 30.0  # seconds before giving up on a single Ollama call


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
    last_exc: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                format="json",
                options={"temperature": 0},
            )
            content = response["message"]["content"].strip()
            data = json.loads(content)
            return DetectiveVerdict.model_validate(data)

        except (json.JSONDecodeError, ValidationError) as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** (attempt - 1)))

        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** attempt))

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
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(grey_zone_skills))) as ex:
        futures = {
            ex.submit(_resolve_one, skill, raw_text, model, _aliases.get(skill)): skill
            for skill in grey_zone_skills
        }
        for future in as_completed(futures):
            skill = futures[future]
            try:
                verdicts[skill] = future.result(timeout=OLLAMA_TIMEOUT)
            except TimeoutError:
                verdicts[skill] = DetectiveVerdict(
                    classification="NO MATCH",
                    evidence="Ollama call timed out",
                    reasoning=f"No response within {OLLAMA_TIMEOUT}s",
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
