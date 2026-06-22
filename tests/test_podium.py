"""Tests del Podium agent."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.podium import build_entry, compute_score_semantic, rank
from src.agents.qualifier import Penalties, QualifierResult
from src.schemas.vacancy import SkillItem, ToolItem, Vacancy


def _vacancy(vid: int, role: str = "Data Analyst", skills: list | None = None, tools: list | None = None) -> Vacancy:
    return Vacancy(
        id=vid,
        job_title=role,
        sector="Retail",
        years_experience=1,
        has_internship=False,
        highest_degree="Bachelor's",
        tools=tools or [],
        skills=skills or [],
        required_language_list=[],
    )


def _qres(decision="keep", lang=0, exp=0, edu=0, flags=None) -> QualifierResult:
    return QualifierResult(
        decision=decision,
        penalties=Penalties(language=lang, experience=exp, education=edu),
        flags=flags or [],
    )


def _ling(*pairs) -> dict:
    """pairs: (skill_name, classification)"""
    return {"skills": [{"vacancy_skill": n, "classification": c, "best_match": None, "similarity": 0.0} for n, c in pairs]}


def test_ties_broken_by_semantic_score():
    """Dues ofertes mateixa penalització, score_semantic diferent -> guanya el millor semàntic."""
    skills = [SkillItem(name="Python", purpose="dev", type="must_have")]
    vac_a = _vacancy(1, skills=skills)
    vac_b = _vacancy(2, skills=skills)
    qres = _qres(lang=5)
    prof = {"experiencia_anys": 2, "idiomes": {"english": "B1"}, "formacio_nivell": "Grau"}
    off = {"experiencia_min": 1, "experiencia_max": 5, "idioma_requerit": {"english": "B2"}, "formacio_min": "Grau"}

    items = [
        (vac_a, _ling(("Python", "MATCH")), qres, prof, off),       # 100 - 5 = 95
        (vac_b, _ling(("Python", "NO MATCH")), qres, prof, off),   # 0 - 5 = 0
    ]
    top = rank(items)
    assert [e.offer_id for e in top] == [1, 2]
    assert top[0].score_match == 95
    assert top[1].score_match == 0


def test_eliminate_offer_not_in_ranking():
    vac = _vacancy(1, skills=[SkillItem(name="Python", purpose="dev", type="must_have")])
    items = [
        (vac, _ling(("Python", "MATCH")), _qres(decision="eliminate", flags=["experience_gap_critical"]), {}, {}),
        (vac, _ling(("Python", "MATCH")), _qres(), {}, {}),
    ]
    top = rank(items)
    assert len(top) == 1
    assert top[0].score_match == 100


def test_score_match_subtracts_penalty_total():
    """score_semantic 88, penalty_total 5 -> score_match 83."""
    # Construïm cobertura que doni exactament 88: 4 must_have, 3 MATCH + 1 GREY = 3*2 + 0.5*2 = 7 / 8 = 87.5 → 88
    skills = [SkillItem(name=f"S{i}", purpose="dev", type="must_have") for i in range(4)]
    vac = _vacancy(1, skills=skills)
    ling = _ling(("S0", "MATCH"), ("S1", "MATCH"), ("S2", "MATCH"), ("S3", "GREY ZONE"))
    qres = _qres(lang=5)
    entry = build_entry(vac, ling, qres, {}, {"idioma_requerit": {}})
    assert entry.score_semantic == 88
    assert entry.penalty_total == 5
    assert entry.score_match == 83


def test_score_match_clamped_at_zero():
    """score_semantic 10, penalty_total 30 -> 0 (no negatiu)."""
    skills = [SkillItem(name="S", purpose="dev", type="must_have")]
    vac = _vacancy(1, skills=skills)
    # NO MATCH -> 0% cobertura -> score_semantic 0
    ling = _ling(("S", "NO MATCH"))
    qres = _qres(lang=12, exp=12, edu=8)
    prof = {"experiencia_anys": 1, "idiomes": {}, "formacio_nivell": "FP"}
    off = {"experiencia_min": 3, "experiencia_max": 7, "idioma_requerit": {"english": "C1"}, "formacio_min": "Master"}
    entry = build_entry(vac, ling, qres, prof, off)
    assert entry.penalty_total == 32
    assert entry.score_match == 0  # clamp


def test_reasons_filled_for_penalised_axes_null_otherwise():
    vac = _vacancy(1, skills=[SkillItem(name="Python", purpose="dev", type="must_have")])
    qres = _qres(lang=5, exp=0, edu=4)
    prof = {"experiencia_anys": 3, "idiomes": {"english": "B1"}, "formacio_nivell": "Grau"}
    off = {"experiencia_min": 2, "experiencia_max": 5, "idioma_requerit": {"english": "B2"}, "formacio_min": "Master"}
    entry = build_entry(vac, _ling(("Python", "MATCH")), qres, prof, off)

    assert entry.reasons.language is not None
    assert "B2" in entry.reasons.language and "B1" in entry.reasons.language and "−5" in entry.reasons.language
    assert entry.reasons.experience is None  # penalització 0
    assert entry.reasons.education is not None
    assert "Master" in entry.reasons.education and "Grau" in entry.reasons.education


def test_must_have_weighted_more_than_nice_to_have():
    """1 must-have NO MATCH (pes 2) + 1 nice-to-have MATCH (pes 1) -> 1/3 * 100 = 33."""
    skills = [
        SkillItem(name="Must", purpose="dev", type="must_have"),
        SkillItem(name="Nice", purpose="dev", type="nice_to_have"),
    ]
    vac = _vacancy(1, skills=skills)
    ling = _ling(("Must", "NO MATCH"), ("Nice", "MATCH"))
    assert compute_score_semantic(vac, ling) == 33
