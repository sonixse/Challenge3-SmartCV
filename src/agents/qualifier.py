"""Qualifier agent — graduated penalty system (deterministic, no LLM).

For each (candidate, offer) pair, returns a `QualifierResult` with a hard
keep/eliminate decision plus per-axis graduated penalties. Elimination can
only come from an extreme gap on a SINGLE axis (language or experience),
never from the sum of penalties. Education never eliminates on its own.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# CEFR proficiency ordering — used to compute the integer "gap" between
# the level required by the offer and the candidate's actual level.
CEFR: dict[str, int] = {
    "A1": 1, "A2": 2,
    "B1": 3, "B2": 4,
    "C1": 5, "C2": 6,
}

# Education ordering (Catalan/Spanish labels expected by the offer schema).
# Unknown labels are treated as gap=0 + an `education_unknown` flag so the
# pipeline can keep going without forcing a wrong elimination.
EDU: dict[str, int] = {
    "FP": 1,
    "Grau": 2,
    "Master": 3,
    "Doctorat": 4,
}


class CandidateInput(BaseModel):
    """Minimal candidate view the Qualifier needs (subset of the Interpreter output)."""
    experiencia_anys: float = Field(ge=0)
    idiomes: dict[str, str] = Field(default_factory=dict)  # {idioma: CEFR}
    formacio_nivell: Optional[str] = None


class OfferInput(BaseModel):
    """Minimal offer view the Qualifier needs."""
    experiencia_min: int = Field(ge=0)
    experiencia_max: int = Field(ge=0)
    idioma_requerit: dict[str, str] = Field(default_factory=dict)  # {idioma: CEFR min}
    formacio_min: Optional[str] = None


class Penalties(BaseModel):
    language: int = 0
    experience: int = 0
    education: int = 0


class QualifierResult(BaseModel):
    decision: Literal["keep", "eliminate"]
    penalties: Penalties
    flags: list[str] = Field(default_factory=list)


def _language_axis(
    cand_langs: dict[str, str],
    required: dict[str, str],
) -> tuple[int, bool, list[str]]:
    """Return (penalty, eliminate, flags) for the language axis.

    Threshold rationale:
      gap 1  -> 5   (one CEFR step, recoverable on the job)
      gap 2  -> 12  (two steps, serious but not disqualifying)
      gap>=3 -> ELIMINATE (three steps means the candidate cannot operate)
    Missing language on the candidate side is treated as level 0 so the
    gap equals the full required level.
    """
    if not required:
        return 0, False, []

    flags: list[str] = []
    worst_gap = 0
    cand_norm = {k.lower(): v for k, v in cand_langs.items()}

    for lang, req_level in required.items():
        req_rank = CEFR.get(req_level, 0)
        cand_level = cand_norm.get(lang.lower())
        cand_rank = CEFR.get(cand_level, 0) if cand_level else 0
        gap = req_rank - cand_rank
        if gap > worst_gap:
            worst_gap = gap

    if worst_gap <= 0:
        return 0, False, flags
    if worst_gap == 1:
        return 5, False, flags
    if worst_gap == 2:
        return 12, False, flags
    flags.append("language_gap_critical")
    return 0, True, flags


def _experience_axis(
    years: float,
    exp_min: int,
    exp_max: int,
) -> tuple[int, bool, list[str]]:
    """Return (penalty, eliminate, flags) for the experience axis.

    Rationale:
      Inside [min, max]                 -> 0
      Over max                           -> 0 + overqualified flag (never penalize up)
      gap <= 1 year                      -> 5  (close enough, soft penalty)
      gap > 1 and not extreme            -> 12 (significant shortfall)
      years < min - max(2, 0.5*min)      -> ELIMINATE (extreme shortfall)
    """
    flags: list[str] = []

    if years > exp_max and exp_max > 0:
        flags.append("overqualified_experience")
        return 0, False, flags

    if years >= exp_min:
        return 0, False, flags

    gap = exp_min - years
    elim_threshold = exp_min - max(2.0, 0.5 * exp_min)
    if years < elim_threshold:
        flags.append("experience_gap_critical")
        return 0, True, flags

    if gap <= 1:
        return 5, False, flags
    return 12, False, flags


def _education_axis(
    cand_level: Optional[str],
    required: Optional[str],
) -> tuple[int, list[str]]:
    """Return (penalty, flags) for the education axis. Never eliminates.

    Rationale:
      gap == 1 -> 4  (one degree below, often offset by experience)
      gap >= 2 -> 8  (clearly below, but skills can compensate)
    """
    flags: list[str] = []
    if not required:
        return 0, flags

    req_rank = EDU.get(required)
    cand_rank = EDU.get(cand_level) if cand_level else None

    if req_rank is None or cand_rank is None:
        flags.append("education_unknown")
        return 0, flags

    gap = req_rank - cand_rank
    if gap <= 0:
        return 0, flags
    if gap == 1:
        return 4, flags
    return 8, flags


def qualify(profile: CandidateInput | dict, offer: OfferInput | dict) -> QualifierResult:
    """Pure function: judge a candidate against one offer.

    Elimination is per-axis only; penalties never sum into an elimination.
    """
    prof = profile if isinstance(profile, CandidateInput) else CandidateInput(**profile)
    off = offer if isinstance(offer, OfferInput) else OfferInput(**offer)

    lang_pen, lang_elim, lang_flags = _language_axis(prof.idiomes, off.idioma_requerit)
    exp_pen, exp_elim, exp_flags = _experience_axis(
        prof.experiencia_anys, off.experiencia_min, off.experiencia_max
    )
    edu_pen, edu_flags = _education_axis(prof.formacio_nivell, off.formacio_min)

    decision: Literal["keep", "eliminate"] = (
        "eliminate" if (lang_elim or exp_elim) else "keep"
    )

    return QualifierResult(
        decision=decision,
        penalties=Penalties(language=lang_pen, experience=exp_pen, education=edu_pen),
        flags=[*lang_flags, *exp_flags, *edu_flags],
    )
