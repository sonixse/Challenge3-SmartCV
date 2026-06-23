"""Visionary agent: Gap analysis and career coaching from Podium ranking.

Two-step process:
  1. Deterministic: aggregate NO MATCH skill frequency across top-N offers,
     identify strengths (MATCH skills appearing in ≥2 top offers).
  2. One Ollama call: generate actionable coaching advice in JSON.

Expected podium_result shape:
    {"ranking": [{"offer_id": int, "role": str, "score_match": int, ...}, ...]}

Expected linguist_result shape:
    {"by_offer": {str(offer_id): {"match": [...], "grey_zone": [...], "no_match": [...]}, ...}}
"""

import json
import time
from collections import Counter

import ollama
from pydantic import BaseModel

from src.config import MAX_RETRIES, RETRY_DELAY, VISIONARY_TOP_N as TOP_N


class GapItem(BaseModel):
    skill: str
    frequency: int       # number of top offers where this skill is NO MATCH
    offer_ids: list[int]


class VisionaryResult(BaseModel):
    top_gaps: list[GapItem]  # sorted by frequency desc
    strengths: list[str]      # skills matching well across top offers
    coaching: str             # LLM-generated advice
    best_fit_role: str
    best_fit_score: int


_SYSTEM_PROMPT = """\
You are a career coach specialising in CV optimisation. Given a candidate profile \
and the skills they are missing for their best-matching job offers, write concise, \
actionable coaching advice (3-5 sentences). Focus on the most impactful skill gaps \
and be encouraging but realistic.
Return ONLY valid JSON: {"coaching": "your advice here"}"""


def _aggregate_gaps(
    podium_entries: list[dict],
    linguist_by_offer: dict[str, dict],
    top_n: int = TOP_N,
) -> tuple[list[GapItem], list[str]]:
    """Count NO MATCH frequency and identify strengths across top-N offers."""
    top_entries = podium_entries[:top_n]
    gap_offers: dict[str, list[int]] = {}
    match_counter: Counter = Counter()

    for entry in top_entries:
        offer_id = str(entry["offer_id"])
        ling = linguist_by_offer.get(offer_id, {})

        for skill in ling.get("no_match", []):
            gap_offers.setdefault(skill, []).append(entry["offer_id"])

        for skill in ling.get("match", []):
            match_counter[skill] += 1

    gaps = [
        GapItem(skill=skill, frequency=len(ids), offer_ids=ids)
        for skill, ids in gap_offers.items()
    ]
    gaps.sort(key=lambda g: g.frequency, reverse=True)

    # threshold scales with how many offers survived: at least 1/3 of top entries
    threshold = max(1, len(top_entries) // 3)
    strengths = [skill for skill, count in match_counter.most_common() if count >= threshold]

    return gaps, strengths


def _call_llm(
    candidate_name: str,
    best_fit_role: str,
    best_fit_score: int,
    top_gaps: list[GapItem],
    strengths: list[str],
    model: str,
) -> str:
    """One Ollama call to generate coaching advice. Returns the coaching string."""
    gap_list      = ", ".join(g.skill for g in top_gaps[:5]) or "none identified"
    strength_list = ", ".join(strengths[:5]) or "none identified"

    user_msg = (
        f"Candidate: {candidate_name}\n"
        f"Best matching role: {best_fit_role} (score {best_fit_score}/100)\n"
        f"Top skill gaps (missing in best-matching offers): {gap_list}\n"
        f"Key strengths (matching across top offers): {strength_list}\n\n"
        "Write career coaching advice."
    )

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
                options={"temperature": 0.3},
            )
            content = response["message"]["content"].strip()
            data = json.loads(content)
            coaching = data.get("coaching", "").strip()
            if coaching:
                return coaching
            raise ValueError("Empty coaching field in LLM response")

        except (json.JSONDecodeError, ValueError) as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** (attempt - 1)))

        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

    return f"Could not generate coaching advice: {last_exc}"


def analyse(
    candidate_name: str,
    podium_result: dict,
    linguist_result: dict,
    model: str = "llama3",
) -> VisionaryResult:
    """Full Visionary analysis for one candidate.

    Args:
        candidate_name:  CandidateProfile.name
        podium_result:   {"ranking": [...]} from Podium
        linguist_result: {"by_offer": {str(offer_id): linguist_analyse_dict, ...}}
        model:           Ollama model name
    """
    ranking: list[dict] = podium_result.get("ranking", [])
    by_offer: dict      = linguist_result.get("by_offer", {})

    if not ranking:
        return VisionaryResult(
            top_gaps=[], strengths=[], coaching="No matching offers found.",
            best_fit_role="None", best_fit_score=0,
        )

    top_gaps, strengths = _aggregate_gaps(ranking, by_offer)

    best           = ranking[0]
    best_fit_role  = best.get("role", "Unknown")
    best_fit_score = best.get("score_match", 0)

    coaching = _call_llm(
        candidate_name=candidate_name,
        best_fit_role=best_fit_role,
        best_fit_score=best_fit_score,
        top_gaps=top_gaps,
        strengths=strengths,
        model=model,
    )

    return VisionaryResult(
        top_gaps=top_gaps,
        strengths=strengths,
        coaching=coaching,
        best_fit_role=best_fit_role,
        best_fit_score=best_fit_score,
    )
