"""Agent 1 — Extractor de CV.

Pipeline:
    PDF  ->  text (pdf_reader)  ->  Groq LLM  ->  JSON  ->  Pydantic CV
"""

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError

from models import CV
from pdf_reader import extract_text

# Mateixos models que utilitza el chatbot de l'equip (chat/generate.py).
DEFAULT_MODEL = "llama-3.1-8b-instant"
FALLBACK_MODEL = "llama-3.3-70b-versatile"

# Esquema d'exemple inline per al prompt: més fiable que descriure-ho amb text,
# i alineat amb ofertes.json perquè el matching posterior sigui directe.
_JSON_SCHEMA_EXAMPLE = """{
  "skills": [{"name": "A/B Testing", "purpose": "analysis"}],
  "tools":  [{"name": "SQL", "purpose": "querying"}],
  "years_experience": 0,
  "highest_degree": "",
  "experience": [
    {"role": "Data Analyst", "company": "ACME", "duration": "2020-2023", "description": null}
  ],
  "education": [
    {"degree": "Grau en Informàtica", "institution": "UPC", "year": "2019"}
  ]
}"""

_SYSTEM_PROMPT = (
    "Ets un extractor d'informació de CVs. Reps el text pla d'un CV i n'extreus "
    "skills, tools, experiència i formació. Has de respondre EXCLUSIVAMENT amb "
    "un objecte JSON vàlid, sense text addicional, sense explicacions i sense "
    "blocs de Markdown (no posis ```json ni ```). Si un camp no es pot "
    "determinar, posa una llista buida o una cadena buida; per a "
    "years_experience usa 0 si no es pot deduir."
)


def _build_user_prompt(cv_text: str) -> str:
    return (
        "Extreu les dades del següent CV i retorna-les en aquest format JSON exacte:\n\n"
        f"{_JSON_SCHEMA_EXAMPLE}\n\n"
        "Regles:\n"
        "- `purpose` és una categoria curta (ex: 'analysis', 'querying', "
        "'programming', 'visualization', 'soft', 'cloud').\n"
        "- Separa hard skills/competències a `skills` i eines/tecnologies a `tools`.\n"
        "- `highest_degree` és el títol acadèmic més alt en una sola línia.\n"
        "- `years_experience` és un enter (suma aproximada d'anys d'experiència professional).\n\n"
        "TEXT DEL CV:\n"
        "-------------\n"
        f"{cv_text}\n"
        "-------------\n"
        "Retorna NOMÉS el JSON."
    )


def _strip_markdown_fences(raw: str) -> str:
    """Neteja ```json ... ``` per si el model els afegeix tot i les instruccions."""
    txt = raw.strip()
    # Treu fences de codi al principi/final.
    txt = re.sub(r"^```(?:json)?\s*", "", txt)
    txt = re.sub(r"\s*```$", "", txt)
    return txt.strip()


def _extract_first_json_object(raw: str) -> str:
    """Retorna la primera { ... } balancejada — útil si el model afegeix text."""
    start = raw.find("{")
    if start == -1:
        return raw
    depth = 0
    for i in range(start, len(raw)):
        ch = raw[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start:i + 1]
    return raw  # malformat; deixem que json.loads expliqui l'error


def _call_groq(client: Groq, model: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,  # extracció determinista
        # response_format JSON: Groq el suporta en els models Llama 3.x.
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def extract_cv(pdf_path: str, model: str = DEFAULT_MODEL) -> CV:
    """Extreu un CV validat des d'un PDF."""
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GROQ_API_KEY al .env")

    client = Groq(api_key=api_key)

    cv_text = extract_text(pdf_path)
    if not cv_text:
        raise ValueError("No s'ha pogut extreure text del PDF (buit després d'OCR).")

    user_prompt = _build_user_prompt(cv_text)
    raw = _call_groq(client, model, user_prompt)

    # 1r intent: parse directe.
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 2n intent: netejar fences i retallar al primer JSON balancejat.
        cleaned = _extract_first_json_object(_strip_markdown_fences(raw))
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # 3r intent: reintent amb el model més gran, demanant explícitament
            # que corregeixi el format.
            retry_prompt = (
                "La teva resposta anterior no era JSON vàlid. Torna-la a generar "
                "com a objecte JSON pur, sense res més.\n\nResposta anterior:\n"
                f"{raw}"
            )
            raw2 = _call_groq(client, FALLBACK_MODEL, retry_prompt)
            data = json.loads(_extract_first_json_object(_strip_markdown_fences(raw2)))

    try:
        return CV(**data)
    except ValidationError as e:
        raise ValueError(f"JSON del LLM no compleix l'esquema CV:\n{e}") from e


if __name__ == "__main__":
    # Bloc de prova: passa la ruta del PDF com a argument o edita SAMPLE.
    SAMPLE = "sample_cv.pdf"
    pdf = sys.argv[1] if len(sys.argv) > 1 else SAMPLE

    if not Path(pdf).exists():
        print(f"[!] No hi ha PDF a '{pdf}'. Passa la ruta: python extractor.py <ruta.pdf>")
        sys.exit(1)

    cv = extract_cv(pdf)
    print(json.dumps(cv.model_dump(), indent=2, ensure_ascii=False))
