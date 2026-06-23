"""CV Advisor chat — wraps ollama.chat with a system prompt built from
the Detective analysis, the candidate profile, and the ranking results.
"""

import ollama

from src.schemas.candidate import CandidateProfile
from src.agents.podium import PodiumEntry


def build_context(
    profile: CandidateProfile,
    ranking: list[PodiumEntry],
    detective_knowledge: dict[str, dict],
) -> str:
    """Build the advisor system prompt from pipeline results.

    Args:
        profile:             validated CandidateProfile
        ranking:             top PodiumEntry list from compute_ranking()
        detective_knowledge: {skill: {classification, reasoning}} accumulated
                             across all vacancies during the ranking run
    """
    skills_str  = ", ".join(s.name for s in profile.skills[:12]) or "cap skill detectada"
    langs_str   = ", ".join(f"{l.language} ({l.level})" for l in profile.languages)

    top_offers = "\n".join(
        f"  • {e.role} ({e.sector}) — {e.score_match}% match"
        for e in ranking[:5]
    ) or "  Cap oferta ha superat el filtre mínim."

    gaps = {
        skill: info["reasoning"]
        for skill, info in detective_knowledge.items()
        if info.get("classification") == "NO MATCH"
    }
    gaps_str = "\n".join(
        f"  • {skill}: {reasoning}"
        for skill, reasoning in gaps.items()
    ) or "  Cap gap crític identificat."

    return f"""\
Ets un assessor de carrera especialitzat en CVs del sector tecnològic i de dades.
Ajudes {profile.name} a entendre els resultats del seu CV i a millorar-lo.

PERFIL DEL CANDIDAT:
  Nom: {profile.name}
  Experiència: {profile.years_experience} anys
  Formació: {profile.education_level} en {profile.education_field}
  Skills actuals: {skills_str}
  Idiomes: {langs_str}

TOP OFERTES (per compatibilitat):
{top_offers}

ANÀLISI DE GAPS (skills que demanen les ofertes però no es veuen clarament al CV):
{gaps_str}

EL TEU ROL:
  - Explica PER QUÈ el score és baix per a certes ofertes.
  - Dona consells CONCRETS i ACCIONABLES sobre com millorar el CV.
  - Indica quines skills estan més demanades i com cal afegir-les.
  - Respon SEMPRE en l'idioma en què t'escriu l'usuari (català, castellà, anglès...).
  - Sigues concís: màxim 3-4 punts per resposta.\
"""


def advisor_respond(
    message: str,
    history: list[dict],
    system_prompt: str,
    model: str = "llama3",
) -> str:
    """Send a message to the advisor and return the response.

    Args:
        message:       new user message
        history:       list of {role, content} dicts (without the new message)
        system_prompt: pre-built context from build_context()
        model:         Ollama model name
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    try:
        response = ollama.chat(model=model, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        return f"Error connectant amb Ollama: {e}"
