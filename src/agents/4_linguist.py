"""
General pseudocode

for each vacancy skill requirement:
    embed the skill name with BGE (BAAI General Embedding)
    compute cosine similarity against each candidate skill vector (embedded on the fly)
    take the highest similarity score
    classify: MATCH / GREY ZONE / NO MATCH
"""

# Linguist agent - Semantic skills comparison using BGE embeddings + ChromaDB

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# run from root folder: python src/agents/4_linguist.py

"""
Semantic skills comparison.

Two-step process:
  1. Chroma query  -> coarse retrieval: find top-K most relevant vacancies for the candidate
  2. Per-skill BGE -> fine-grained: for each vacancy skill, compare against all candidate skills
                        and classify as MATCH / GREY ZONE / NO MATCH
"""

import numpy as np
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from src.schemas.candidate import CandidateProfile, CandidateSkill, CandidateLanguage
from src.schemas.vacancy import Vacancy
from src.data.load_vacancies import load

# Model (loaded once at module level)

# In production move it to a shared singleton 
# so multiple agents could share the same loaded model

_MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")

# Thresholds
MATCH_THRESHOLD    = 0.85   # cosine similarity above this → MATCH
GREY_ZONE_THRESHOLD = 0.60  # between this and MATCH → GREY ZONE, below → NO MATCH

# ChromaDB
_CHROMA_CLIENT = chromadb.PersistentClient(path="data/chroma")
_EF = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5",
    normalize_embeddings=True
)
_COLLECTION = _CHROMA_CLIENT.get_collection(name="vacancies", embedding_function=_EF)


def _embed(text: str) -> np.ndarray:
    """Embed a single string with BGE and return a normalized numpy vector."""
    vec = _MODEL.encode(text, normalize_embeddings=True)
    return np.array(vec)

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two normalized vectors (dot product suffices)."""
    return float(np.dot(a, b))

def _classify(score: float) -> str:
    if score >= MATCH_THRESHOLD:
        return "MATCH"
    elif score >= GREY_ZONE_THRESHOLD:
        return "GREY ZONE"
    else:
        return "NO MATCH"

def retrieve_top_k(candidate: CandidateProfile, k: int = 50) -> list[str]:
    """
    Step 1. Chroma coarse retrieval.
    Build a candidate query string and return the top-K vacancy IDs from Chroma.
    """
    skill_text = ", ".join(s.name for s in candidate.skills)
    query = (
        f"Candidate with {candidate.years_experience} years of experience. "
        f"Education: {candidate.education_level} in {candidate.education_field}. "
        f"Skills: {skill_text}."
    )
    results = _COLLECTION.query(query_texts=[query], n_results=k)
    return results["ids"][0]   # list of vacancy IDs (strings)


def compare_skills(candidate: CandidateProfile, vacancy: Vacancy) -> list[dict]:
    """
    Step 2. Per-skill BGE fine-grained comparison.

    For each required skill in the vacancy, find the best-matching candidate skill
    and classify the pair as MATCH / GREY ZONE / NO MATCH.

    Returns a list of dicts, one per vacancy skill:
        {
          "vacancy_skill":    str,
          "best_match":       str,   — candidate skill with highest similarity
          "similarity":       float, — cosine similarity score
          "classification":   str,   — "MATCH" | "GREY ZONE" | "NO MATCH"
        }
    """
    # Embed all candidate skills once
    candidate_vecs = [
        (s.name, _embed(s.name)) for s in candidate.skills
    ]

    results = []
    vacancy_skills = list(vacancy.skills) + list(vacancy.tools)

    for req in vacancy_skills:
        req_vec = _embed(req.name)

        # Find best-matching candidate skill
        best_skill = None
        best_score = -1.0
        for cand_name, cand_vec in candidate_vecs:
            score = _cosine(req_vec, cand_vec)
            if score > best_score:
                best_score = score
                best_skill = cand_name

        results.append({
            "vacancy_skill":  req.name,
            "best_match":     best_skill,
            "similarity":     round(best_score, 4),
            "classification": _classify(best_score),
        })

    return results


def analyse(candidate: CandidateProfile, vacancy: Vacancy) -> dict:
    """
    Alan Turing: full analysis for one candidate against one vacancy.

    Returns:
        {
          "skills":     list[dict]  — per-skill classification (see compare_skills)
          "match":      list[str]   — vacancy skills classified as MATCH
          "grey_zone":  list[str]   — vacancy skills classified as GREY ZONE
          "no_match":   list[str]   — vacancy skills classified as NO MATCH
          "summary":    dict        — counts per category
        }
    """
    skills = compare_skills(candidate, vacancy)

    match     = [s["vacancy_skill"] for s in skills if s["classification"] == "MATCH"]
    grey_zone = [s["vacancy_skill"] for s in skills if s["classification"] == "GREY ZONE"]
    no_match  = [s["vacancy_skill"] for s in skills if s["classification"] == "NO MATCH"]

    return {
        "skills":    skills,
        "match":     match,
        "grey_zone": grey_zone,
        "no_match":  no_match,
        "summary": {
            "total":     len(skills),
            "match":     len(match),
            "grey_zone": len(grey_zone),
            "no_match":  len(no_match),
        }
    }


if __name__ == "__main__":

    # Test
    candidate = CandidateProfile(
        name="Juan López",
        skills=[
            CandidateSkill(name="Python"),
            CandidateSkill(name="scikit-learn"),
            CandidateSkill(name="SQL"),
        ],
        years_experience=2,
        education_level="Bachelor's",
        education_field="Computer Science",
        languages=[
            CandidateLanguage(language="Spanish", level="Native"),
            CandidateLanguage(language="English", level="B2"),
        ],
        raw_text="Junior data scientist with Python and ML experience.",
    )

    _, vacancies = load()

    # Step 1: Chroma retrieval
    print(f"Step 1 — Retrieving top 5 vacancies from Chroma for {candidate.name}...\n")
    top_ids = retrieve_top_k(candidate, k=5)
    top_vacancies = [v for v in vacancies if str(vacancies.index(v)) in top_ids]

    # Step 2: Per-skill analysis on first retrieved vacancy
    if top_vacancies:
        vac = top_vacancies[0]
        print(f"Step 2 — Per-skill analysis: {vac.job_title} @ {vac.sector}\n")
        result = analyse(candidate, vac)

        print(f"  MATCH     ({result['summary']['match']}): {result['match']}")
        print(f"  GREY ZONE ({result['summary']['grey_zone']}): {result['grey_zone']}")
        print(f"  NO MATCH  ({result['summary']['no_match']}): {result['no_match']}")
        print(f"\nPer-skill detail:")
        for s in result["skills"]:
            icon = {"MATCH": "✅", "GREY ZONE": "⚠️ ", "NO MATCH": "❌"}[s["classification"]]
            print(f"  {icon} {s['vacancy_skill']:<30} ← {s['best_match']:<20} ({s['similarity']})")