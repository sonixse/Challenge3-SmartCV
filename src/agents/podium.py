"""Podium agent — agrega Linguist (semàntic) + Qualifier (penalitzacions) en un
`score_match` positiu 0-100 i ordena les ofertes descendent.

Codi 100% determinista (cap LLM). El `score_semantic` és la cobertura ponderada
de skills/eines de l'oferta (must-have pesa més que nice-to-have); el `score_match`
final es calcula restant les penalitzacions del Qualifier.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from src.agents.qualifier import CEFR, QualifierResult
from src.schemas.vacancy import Vacancy


# Pesos per agregar la cobertura de skills. Must-have val el doble que la resta
# perquè perdre'n una és més greu que perdre una eina o un nice-to-have.

from src.config import (
    PODIUM_WEIGHT_MUST  as _WEIGHT_MUST_HAVE,
    PODIUM_WEIGHT_NICE  as _WEIGHT_NICE_TO_HAVE,
    PODIUM_WEIGHT_OTHER as _WEIGHT_OTHER,
    PODIUM_CREDIT_MATCH, PODIUM_CREDIT_GREY, PODIUM_CREDIT_NO,
)
_CREDIT = {"MATCH": PODIUM_CREDIT_MATCH, 
           "GREY ZONE": PODIUM_CREDIT_GREY, 
           "NO MATCH": PODIUM_CREDIT_NO}


class PodiumPenalties(BaseModel):
    language: int = 0
    experience: int = 0
    education: int = 0


class PodiumReasons(BaseModel):
    language: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None


class PodiumEntry(BaseModel):
    offer_id: int
    role: str
    sector: str
    score_match: int = Field(ge=0, le=100)
    score_semantic: int = Field(ge=0, le=100)
    penalties: PodiumPenalties
    penalty_total: int
    flags: list[str] = Field(default_factory=list)
    reasons: PodiumReasons


def compute_score_semantic(vacancy: Vacancy, linguist_result: dict) -> int:
    """Cobertura ponderada de les skills/eines de l'oferta.

    Fórmula:
        score = Σ(weight·credit) / Σ(weight) · 100

      - weight: 2.0 must-have, 1.0 nice-to-have, 1.0 tool/other
      - credit: 1.0 MATCH, 0.5 GREY ZONE, 0.0 NO MATCH

    Si l'oferta no té skills/eines retorna 0.
    """
    type_by_name: dict[str, str] = {}
    for s in vacancy.skills:
        type_by_name[s.name.lower()] = s.type or "skill_untyped"
    for t in vacancy.tools:
        type_by_name[t.name.lower()] = "tool"

    skills = linguist_result.get("skills", [])
    if not skills:
        return 0

    weighted_sum = 0.0
    total_weight = 0.0
    for entry in skills:
        kind = type_by_name.get(entry["vacancy_skill"].lower(), "skill_untyped")
        if kind == "must_have":
            w = _WEIGHT_MUST_HAVE
        elif kind == "nice_to_have":
            w = _WEIGHT_NICE_TO_HAVE
        else:
            w = _WEIGHT_OTHER
        credit = _CREDIT.get(entry["classification"], 0.0)
        weighted_sum += w * credit
        total_weight += w

    if total_weight == 0:
        return 0
    return int(round((weighted_sum / total_weight) * 100))


def _reason_language(profile: dict, offer: dict, penalty: int) -> Optional[str]:
    """Frase amb el pitjor gap d'idioma. Format: 'Idioma −5 · English B2 demanat, tens B1'."""
    if penalty == 0:
        return None
    required = offer.get("idioma_requerit", {})
    cand_norm = {k.lower(): v for k, v in profile.get("idiomes", {}).items()}

    worst_lang, worst_req, worst_cand, worst_gap = None, None, None, 0
    for lang, req_level in required.items():
        req_rank = CEFR.get(req_level, 0)
        cand_level = cand_norm.get(lang.lower())
        cand_rank = CEFR.get(cand_level, 0) if cand_level else 0
        gap = req_rank - cand_rank
        if gap > worst_gap:
            worst_lang, worst_req, worst_cand, worst_gap = lang, req_level, cand_level, gap

    if worst_lang is None:
        return f"Idioma −{penalty}"
    cand_label = worst_cand or "no el tens"
    return f"Idioma −{penalty} · {worst_lang.capitalize()} {worst_req} demanat, tens {cand_label}"


def _reason_experience(profile: dict, offer: dict, penalty: int, flags: list[str]) -> Optional[str]:
    """Frase del gap d'experiència. Sobrequalificació no es presenta com a descompte."""
    if "overqualified_experience" in flags:
        return None
    if penalty == 0:
        return None
    years = profile.get("experiencia_anys", 0)
    exp_min = offer.get("experiencia_min", 0)
    return f"Experiència −{penalty} · demana {exp_min} anys, tens {years:g}"


def _reason_education(profile: dict, offer: dict, penalty: int, flags: list[str]) -> Optional[str]:
    if penalty == 0:
        return None
    if "education_unknown" in flags:
        return f"Formació −{penalty} · nivell no reconegut"
    required = offer.get("formacio_min")
    cand_level = profile.get("formacio_nivell") or "sense títol"
    return f"Formació −{penalty} · demana {required}, tens {cand_level}"


def build_entry(
    vacancy: Vacancy,
    linguist_result: dict,
    qualifier_result: QualifierResult,
    qualifier_input_profile: dict,
    qualifier_input_offer: dict,
) -> Optional[PodiumEntry]:
    """Construeix una `PodiumEntry`. Retorna None si decision == eliminate."""
    if qualifier_result.decision == "eliminate":
        return None

    score_semantic = compute_score_semantic(vacancy, linguist_result)
    pen = qualifier_result.penalties
    penalty_total = pen.language + pen.experience + pen.education
    score_match = max(0, min(100, score_semantic - penalty_total))

    reasons = PodiumReasons(
        language=_reason_language(qualifier_input_profile, qualifier_input_offer, pen.language),
        experience=_reason_experience(
            qualifier_input_profile, qualifier_input_offer, pen.experience, qualifier_result.flags
        ),
        education=_reason_education(
            qualifier_input_profile, qualifier_input_offer, pen.education, qualifier_result.flags
        ),
    )

    return PodiumEntry(
        offer_id=vacancy.id,
        role=vacancy.job_title,
        sector=vacancy.sector,
        score_match=score_match,
        score_semantic=score_semantic,
        penalties=PodiumPenalties(
            language=pen.language, experience=pen.experience, education=pen.education
        ),
        penalty_total=penalty_total,
        flags=list(qualifier_result.flags),
        reasons=reasons,
    )


def rank(
    items: list[tuple[Vacancy, dict, QualifierResult, dict, dict]],
    top_n: int = 10,
) -> list[PodiumEntry]:
    """Construeix entries per cada (vacancy, linguist, qualifier, profile_in, offer_in)
    i retorna el top-N ordenat per `score_match` descendent. Filtra els `eliminate`.
    """
    entries: list[PodiumEntry] = []
    for vac, ling, qres, prof_in, off_in in items:
        entry = build_entry(vac, ling, qres, prof_in, off_in)
        if entry is not None:
            entries.append(entry)

    entries.sort(key=lambda e: e.score_match, reverse=True)
    return entries[:top_n]
