"""
Validation / diagnostic script for the matching pipeline.

Runs:
  1. Load a processed candidate from data/processed/
  2. Use linguist.retrieve_top_k to get top-K vacancy IDs from Chroma
  3. For the top 10, print per-vacancy:
        - title + sector
        - semantic similarity score (re-queried directly from the collection,
          since retrieve_top_k discards distances)
        - skill breakdown (MATCH / GREY ZONE / NO MATCH) via linguist.analyse
        - qualifier output (pass, score, failed_checks, reasons)
  4. Print summary of how many distinct job titles appear in the top 10.

Run from project root (Challenge3-SmartCV/):
    python scripts/validate_matching.py
    python scripts/validate_matching.py data/processed/01_candidate.json
"""

import sys
import os
import json
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas.candidate import CandidateProfile
from src.data.load_vacancies import load
from src.agents import linguist
from src.agents.qualifier import qualify


DEFAULT_CANDIDATE = "data/processed/01_candidate.json"
TOP_K = 10


def load_candidate(path: str) -> CandidateProfile:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return CandidateProfile.model_validate(data)


def query_with_scores(candidate: CandidateProfile, k: int):
    """Re-issue the same Chroma query as linguist.retrieve_top_k but keep distances."""
    skill_text = ", ".join(s.name for s in candidate.skills)
    query = (
        f"Candidate with {candidate.years_experience} years of experience. "
        f"Education: {candidate.education_level} in {candidate.education_field}. "
        f"Skills: {skill_text}."
    )
    res = linguist._COLLECTION.query(query_texts=[query], n_results=k)
    ids = res["ids"][0]
    distances = res["distances"][0] if res.get("distances") else [None] * len(ids)
    return list(zip(ids, distances))


def main():
    cand_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CANDIDATE

    print("=" * 80)
    print(f"Loading candidate: {cand_path}")
    candidate = load_candidate(cand_path)
    print(f"  Name:       {candidate.name}")
    print(f"  Experience: {candidate.years_experience}y")
    print(f"  Education:  {candidate.education_level} in {candidate.education_field}")
    print(f"  Skills:     {[s.name for s in candidate.skills]}")
    print(f"  Languages:  {[(l.language, l.level) for l in candidate.languages]}")

    print("\nLoading vacancies...")
    _, vacancies = load()
    print(f"  {len(vacancies)} vacancies loaded")

    print(f"\nStep 1 - Chroma retrieve_top_k (k={TOP_K})...")
    top_ids = linguist.retrieve_top_k(candidate, k=TOP_K)
    id_score = query_with_scores(candidate, k=TOP_K)
    # Map id -> (similarity = 1 - cosine_distance) since collection uses normalized BGE
    id_to_sim = {}
    for vid, dist in id_score:
        if dist is None:
            id_to_sim[vid] = None
        else:
            # Chroma default distance is squared-L2 on normalized vectors;
            # cosine_sim ≈ 1 - dist/2. We just report raw distance + approx sim.
            id_to_sim[vid] = (dist, 1.0 - dist / 2.0)

    titles_in_top = []

    for rank, vid in enumerate(top_ids, start=1):
        vac = vacancies[int(vid)]
        titles_in_top.append(vac.job_title)

        sim_info = id_to_sim.get(vid)
        if sim_info is not None:
            dist, sim = sim_info
            sim_str = f"chroma_distance={dist:.4f}  ~cosine_sim={sim:.4f}"
        else:
            sim_str = "n/a"

        print()
        print("-" * 80)
        print(f"#{rank}  [{vid}]  {vac.job_title}  @  {vac.sector}")
        print(f"   {sim_str}")
        print(f"   requires: {vac.years_experience}y exp, degree={vac.highest_degree}, "
              f"langs={[(l.language, l.level) for l in vac.required_language_list]}")

        # Step 2: linguist per-skill analysis
        ling = linguist.analyse(candidate, vac)
        s = ling["summary"]
        print(f"   Linguist  | total={s['total']}  MATCH={s['match']}  "
              f"GREY={s['grey_zone']}  NO_MATCH={s['no_match']}")
        if ling["match"]:
            print(f"     MATCH      : {ling['match']}")
        if ling["grey_zone"]:
            print(f"     GREY ZONE  : {ling['grey_zone']}")
        if ling["no_match"]:
            print(f"     NO MATCH   : {ling['no_match']}")

        # Step 3: qualifier hard filters
        q = qualify(candidate, vac)
        status = "PASS" if q["pass"] else "FAIL"
        print(f"   Qualifier | {status}  score={q['score']}/4  failed={q['failed_checks']}")
        for r in q["reasons"]:
            print(f"     {r.strip()}")

    print()
    print("=" * 80)
    counts = Counter(titles_in_top)
    print(f"Summary of top {TOP_K}: {len(counts)} distinct job titles")
    for title, n in counts.most_common():
        print(f"  {n:>2}x  {title}")

    passed = sum(1 for vid in top_ids if qualify(candidate, vacancies[int(vid)])["pass"])
    print(f"\nQualifier outcome over top {TOP_K}: {passed} PASS, {TOP_K - passed} FAIL")


if __name__ == "__main__":
    main()
