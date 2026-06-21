# Qualifier agent - Rule based system engine: must-have filters + score

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# run from root folder: python src/agents/3_qualifier.py
"""
1. Load vacancies
2. For each vacancy, check must-have skills, years of experience, and education level
3. Score candidates based on match
"""

from src.data.load_vacancies import load
from src.schemas.candidate import CandidateProfile, CandidateSkill, CandidateLanguage
from src.schemas.vacancy import Vacancy

# Education hierarchy: higher index means higher level
_EDUCATION_RANK = {
    "No degree":  0,
    "Bachelor's": 1,
    "Master's":   2,
    "PhD":        3,
}

# Language hierarchy: higher index means higher proficiency
_LANGUAGE_RANK = {
    "Native": 7,
    "C2": 6,
    "C1": 5,
    "B2": 4,
    "B1": 3,
    "A2": 2,
    "A1": 1,
}

def qualify(candidate:CandidateProfile, vacancy:Vacancy) -> dict:

    """
    Marie Curie: evaluates one candidate against one vacancy.
    Returns + Example:
        {
          "pass":    bool   — False = hard disqualification, Turing won't run
          "score":   int    — 0..4, passed to Williams for ranking
          "failed_checks": [str]  — which checks failed: "experience", "education", "language"
                                 Jobs uses this for targeted coaching
          "reasons": [str]  — human-readable explanation of every check
        }
    """

    reasons = []
    failed_checks = []
    score = 0
    discard = False

    # Hard rule #1: Years of experience

    if candidate.years_experience >= vacancy.years_experience:
        score += 1
        reasons.append(
            f"  Experience: {candidate.years_experience}y OK for {vacancy.years_experience}y"
        )
    else:
        discard = True
        failed_checks.append("experience")
        reasons.append(
            f"  Experience: {candidate.years_experience}y F for {vacancy.years_experience}y"
        )
    
    # Hard rule #2: Education level (hierarchy)

    candidate_rank = _EDUCATION_RANK.get(candidate.education_level, 0)
    vacancy_rank = _EDUCATION_RANK.get(vacancy.highest_degree, 0)

    if candidate_rank >= vacancy_rank:
        score += 1
        reasons.append(
            f"  Education: {candidate.education_level} OK for {vacancy.highest_degree}"
        )
    else:
        discard = True
        failed_checks.append("education")
        reasons.append(
            f"  Education: {candidate.education_level} F for {vacancy.highest_degree}"
        )

    # Hard rule #3: Languages
    # Check each required language and its minimum level

    if vacancy.required_language_list:
        candidate_langs = {
            l.language.lower(): _LANGUAGE_RANK.get(l.level,0)
            for l in candidate.languages
        }

        all_met = True
        for req in vacancy.required_language_list:
            req_lang = req.language.lower()
            req_rank = _LANGUAGE_RANK.get(req.level,0)
            cand_rank = candidate_langs.get(req_lang,0)

            if cand_rank >= req_rank:
                cand_level = next(
                    (l.level for l in candidate.languages if l.language.lower() == req_lang),
                    "not listed"
                )
                reasons.append(
                    f"  Language {req.language}: candidate has {cand_level}"
                    f"  (OK: required {req.level})"
                )
            else:
                discard = True
                all_met = False
                cand_level = next(
                    (l.level for l in candidate.languages if l.language.lower() == req_lang),
                    "not listed"
                )
                reasons.append(
                    f"  Language {req.language}: candidate has {cand_level}"
                    f"  (F: required {req.level})"
                )
        if all_met: score += 1
        else: failed_checks.append("language")
    else:
        score += 1
        reasons.append("  No explicit language(s) in the vacant.")

    # Soft rule: skill name overlap (exact match bonus)
    # Linguist agent handles semantic similarity (this just rewards exact matches)

    candidate_skills = {s.name.lower() for s in candidate.skills}
    vacancy_skills = {s.name.lower() for s in vacancy.skills} | \
                 {t.name.lower() for t in vacancy.tools}

    matched = candidate_skills & vacancy_skills
    if matched:
        score += 1
        reasons.append(f"  Skills overlap: {sorted(matched)}")
    else:
        reasons.append(" No exact skill overlap (linguist will check semantics)")
    
    return{
        "pass": not discard, "score": score, 
        "failed_checks": failed_checks, "reasons": reasons
    }
    

if __name__ == "__main__":
    # test example

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

    # load 5 first vacancies and run qualifier
    
    _,vacancies = load()
    print(f"Running agt on {candidate.name} against 5 vacancies...")

    for vac in vacancies[:5]:
        result = qualify(candidate,vac)
        status = "Pass" if result["pass"] else "Fail"
        print(f"\n{status} | {vac.job_title} @ {vac.sector} | score: {result['score']}")

        if result["failed_checks"]:
            print(f"  Failed: {result['failed_checks']}")
        
        for r in result["reasons"]:
            print(r)