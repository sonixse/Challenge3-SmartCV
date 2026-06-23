"""Tests for the Detective agent — all Ollama calls are mocked."""

# pytest tests/test_detective.py


from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from src.agents.detective import resolve


def _mock_response(classification: str, evidence: str = "Found in CV", reasoning: str = "Clear evidence.") -> MagicMock:
    """Build a fake ollama.chat return value."""
    payload = json.dumps({"classification": classification, "evidence": evidence, "reasoning": reasoning})
    msg = MagicMock()
    msg.__getitem__ = lambda self, key: {"message": MagicMock(**{"__getitem__": lambda s, k: payload if k == "content" else None})}[key]
    response = {"message": {"content": payload}}
    mock = MagicMock(return_value=response)
    return mock


RAW_TEXT = "Candidate has 3 years of Python experience. Used scikit-learn for ML projects."


def test_match_when_explicit_evidence():
    response = {"message": {"content": json.dumps({
        "classification": "MATCH",
        "evidence": "3 years of Python experience",
        "reasoning": "Python is explicitly listed.",
    })}}
    with patch("src.agents.detective.ollama.chat", return_value=response):
        result = resolve(["Python"], RAW_TEXT)

    assert "Python" in result.verdicts
    assert result.verdicts["Python"].classification == "MATCH"
    assert result.verdicts["Python"].evidence != ""


def test_no_match_when_no_evidence():
    response = {"message": {"content": json.dumps({
        "classification": "NO MATCH",
        "evidence": "No evidence found",
        "reasoning": "Kubernetes is not mentioned.",
    })}}
    with patch("src.agents.detective.ollama.chat", return_value=response):
        result = resolve(["Kubernetes"], RAW_TEXT)

    assert result.verdicts["Kubernetes"].classification == "NO MATCH"


def test_multiple_skills_resolved():
    responses = [
        {"message": {"content": json.dumps({"classification": "MATCH",    "evidence": "scikit-learn for ML", "reasoning": "Explicit."})}},
        {"message": {"content": json.dumps({"classification": "NO MATCH", "evidence": "No evidence found",   "reasoning": "Not mentioned."})}},
    ]
    with patch("src.agents.detective.ollama.chat", side_effect=responses):
        result = resolve(["scikit-learn", "Spark"], RAW_TEXT)

    assert len(result.verdicts) == 2
    assert all(v.classification in ("MATCH", "NO MATCH") for v in result.verdicts.values())
    assert "GREY ZONE" not in {v.classification for v in result.verdicts.values()}


def test_summary_counts_correct():
    responses = [
        {"message": {"content": json.dumps({"classification": "MATCH",    "evidence": "Python", "reasoning": "Listed."})}},
        {"message": {"content": json.dumps({"classification": "NO MATCH", "evidence": "No evidence found", "reasoning": "Not found."})}},
    ]
    with patch("src.agents.detective.ollama.chat", side_effect=responses):
        result = resolve(["Python", "Spark"], RAW_TEXT)

    assert result.summary["resolved_to_match"]    == 1
    assert result.summary["resolved_to_no_match"] == 1


def test_retry_on_json_error():
    bad_response  = {"message": {"content": "not valid json {{{"}}
    good_response = {"message": {"content": json.dumps({
        "classification": "MATCH",
        "evidence": "Python experience",
        "reasoning": "Found on retry.",
    })}}
    with patch("src.agents.detective.ollama.chat", side_effect=[bad_response, good_response]):
        with patch("src.agents.detective.time.sleep"):  # skip actual sleep
            result = resolve(["Python"], RAW_TEXT)

    assert result.verdicts["Python"].classification == "MATCH"
