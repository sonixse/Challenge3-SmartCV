"""CV Advisor chat — builds a rich system prompt from all agent outputs."""

import ollama

from src.schemas.candidate import CandidateProfile
from src.agents.podium import PodiumEntry


def build_context(
    profile: CandidateProfile,
    ranking: list[PodiumEntry],
    detective_knowledge: dict[str, dict],
) -> str:
    skills_str = ", ".join(s.name for s in profile.skills) or "none detected"
    langs_str  = ", ".join(f"{l.language} ({l.level})" for l in profile.languages) or "none"

    # ── Full ranking with score breakdown ─────────────────────────────
    ranking_lines = []
    for e in ranking:
        line = f"  • #{ranking.index(e)+1} {e.role} ({e.sector}) — {e.score_match}% match"
        line += f" [semantic: {e.score_semantic}%"
        if e.penalty_total:
            line += f", penalties: -{e.penalty_total}"
            if e.reasons.language:
                line += f" | {e.reasons.language}"
            if e.reasons.experience:
                line += f" | {e.reasons.experience}"
            if e.reasons.education:
                line += f" | {e.reasons.education}"
        line += "]"
        if e.flags:
            line += f" flags: {', '.join(e.flags)}"
        ranking_lines.append(line)
    ranking_str = "\n".join(ranking_lines) or "  No offers passed the filters."

    # ── Detective knowledge: per-skill verdicts ────────────────────────
    matched   = [s for s, i in detective_knowledge.items() if i.get("classification") == "MATCH"]
    grey      = [(s, i.get("reasoning","")) for s, i in detective_knowledge.items() if i.get("classification") == "GREY ZONE"]
    no_match  = [(s, i.get("reasoning","")) for s, i in detective_knowledge.items() if i.get("classification") == "NO MATCH"]

    strengths_str = ", ".join(matched) if matched else "none confirmed by Detective"

    grey_str = "\n".join(
        f"  • {s}: {r}" for s, r in grey
    ) or "  None."

    gaps_str = "\n".join(
        f"  • {s}: {r}" for s, r in no_match
    ) or "  No critical gaps identified."

    # ── Vacancy-specific missing skills for top 3 ─────────────────────
    try:
        from src.data.load_vacancies import load as _load
        _, all_vacs = _load()
        vac_by_id = {v.id: v for v in all_vacs}

        top3_detail = []
        for e in ranking[:3]:
            vac = vac_by_id.get(e.offer_id)
            if not vac:
                continue
            req_skills = [s.name for s in vac.skills] + [t.name for t in vac.tools]
            candidate_skill_names = {s.name.lower() for s in profile.skills}
            missing = [r for r in req_skills if r.lower() not in candidate_skill_names]
            top3_detail.append(
                f"  #{ranking.index(e)+1} {e.role} ({e.sector}) — {e.score_match}%\n"
                f"    Required: {', '.join(req_skills[:12])}\n"
                f"    Missing from CV: {', '.join(missing[:10]) or 'none (name-based check)'}"
            )
        top3_str = "\n".join(top3_detail)
    except Exception:
        top3_str = "  (vacancy detail unavailable)"

    return f"""\
You are SmartCV Assessor, an expert career coach specialised in tech and data CVs.
You help {profile.name} understand their ranking results and improve their CV.
Always respond in the same language the user writes in (Catalan, Spanish, or English).
Be concise: max 4 bullet points per answer. Be specific — name exact skills and offers.

CANDIDATE PROFILE:
  Name: {profile.name}
  Experience: {profile.years_experience} years
  Education: {profile.education_level} in {profile.education_field}
  Skills on CV: {skills_str}
  Languages: {langs_str}

FULL RANKING (score_match = semantic_score - penalties):
{ranking_str}

TOP 3 OFFERS — DETAILED SKILL GAP:
{top3_str}

DETECTIVE ANALYSIS (skill-level evidence from CV text):
  Confirmed matches: {strengths_str}

  Grey zones (ambiguous — candidate may have skill but CV doesn't say it clearly):
{grey_str}

  Confirmed gaps (skill demanded by offers but NOT found in CV):
{gaps_str}

YOUR JOB:
  - Explain WHY scores are low for specific offers (point to exact missing skills).
  - Give CONCRETE, ACTIONABLE advice: which skills to add to the CV and how to phrase them.
  - Highlight the candidate's strengths and which offer fits them best.
  - If asked about a specific offer, use the detailed gap data above.
"""


def advisor_respond(
    message: str,
    history: list[dict],
    system_prompt: str,
    model: str = "llama3",
) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    try:
        response = ollama.chat(model=model, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        return f"Cannot connect to Ollama: {e}"
