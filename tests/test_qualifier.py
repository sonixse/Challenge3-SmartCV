"""Tests for the graduated Qualifier agent."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.qualifier import qualify


def _offer(**overrides):
    base = {
        "experiencia_min": 2,
        "experiencia_max": 5,
        "idioma_requerit": {},
        "formacio_min": "Grau",
    }
    base.update(overrides)
    return base


def _profile(**overrides):
    base = {
        "experiencia_anys": 3.0,
        "idiomes": {"ingles": "B2"},
        "formacio_nivell": "Grau",
    }
    base.update(overrides)
    return base


def test_clean_candidate_keeps_with_zero_penalties():
    res = qualify(_profile(), _offer(idioma_requerit={"ingles": "B2"}))
    assert res.decision == "keep"
    assert res.penalties.language == 0
    assert res.penalties.experience == 0
    assert res.penalties.education == 0


def test_lucia_b1_vs_b2_light_language_penalty():
    res = qualify(
        _profile(idiomes={"ingles": "B1"}),
        _offer(idioma_requerit={"ingles": "B2"}),
    )
    assert res.decision == "keep"
    assert res.penalties.language == 5


def test_lucia_b1_vs_c1_strong_language_penalty():
    res = qualify(
        _profile(idiomes={"ingles": "B1"}),
        _offer(idioma_requerit={"ingles": "C1"}),
    )
    assert res.decision == "keep"
    assert res.penalties.language == 12


def test_junior_vs_senior_eliminated_by_experience():
    res = qualify(
        _profile(experiencia_anys=1.0),
        _offer(experiencia_min=5, experiencia_max=10),
    )
    assert res.decision == "eliminate"
    assert "experience_gap_critical" in res.flags


def test_language_three_levels_below_eliminates():
    res = qualify(
        _profile(idiomes={"ingles": "A1"}),
        _offer(idioma_requerit={"ingles": "B2"}),
    )
    assert res.decision == "eliminate"
    assert "language_gap_critical" in res.flags


def test_overqualified_experience_keeps_with_flag():
    res = qualify(
        _profile(experiencia_anys=12.0),
        _offer(experiencia_min=2, experiencia_max=5),
    )
    assert res.decision == "keep"
    assert res.penalties.experience == 0
    assert "overqualified_experience" in res.flags


def test_education_two_levels_below_never_eliminates():
    res = qualify(
        _profile(formacio_nivell="FP"),
        _offer(formacio_min="Doctorat"),
    )
    assert res.decision == "keep"
    assert res.penalties.education == 8


def test_unknown_education_flagged_not_penalized():
    res = qualify(
        _profile(formacio_nivell="SomethingWeird"),
        _offer(formacio_min="Grau"),
    )
    assert res.decision == "keep"
    assert res.penalties.education == 0
    assert "education_unknown" in res.flags


def test_missing_candidate_language_treated_as_zero():
    res = qualify(
        _profile(idiomes={}),
        _offer(idioma_requerit={"ingles": "B1"}),
    )
    # gap = 3 (B1=3 vs 0) -> eliminate
    assert res.decision == "eliminate"


def test_no_required_language_no_penalty():
    res = qualify(
        _profile(idiomes={}),
        _offer(idioma_requerit={}),
    )
    assert res.decision == "keep"
    assert res.penalties.language == 0
