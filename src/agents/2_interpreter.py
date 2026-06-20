import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# run with `python src/agents/2_interpreter.py` from root project folder

import json
import ollama
from pypdf import PdfReader
from pydantic import ValidationError

from src.schemas.candidate import CandidateProfile
import time

# PDF extraction

def extract_text(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    reader = PdfReader(pdf_path)
    pages  = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


# LLM prompt

SYSTEM_PROMPT = """\
You are a CV parser. Given a raw CV text, extract structured information and return ONLY valid JSON. No explanation, no markdown, no code block.

Return this exact JSON structure:
{
  "name": "candidate full name",
  "skills": [
    {"name": "skill name", "years": 2}
  ],
  "years_experience": 3,
  "education_level": "Bachelor's | Master's | PhD | No degree",
  "education_field": "field of study",
  "languages": [
    {"language": "English", "level": "B2"}
  ],
  "raw_text": "<<FULL_CV_TEXT>>"
}

Rules:
- skills: list every technical skill, tool, framework, and methodology you can find.
- years per skill: infer from context if possible, otherwise omit (null).
- years_experience: total professional experience in years (0 if student/no experience).
- education_level: use exactly one of the four allowed values.
- languages: use CEFR levels (A1, A2, B1, B2, C1, C2) or "Native". If no level is stated, infer from context or use "B2" as a conservative default.
- raw_text: copy the FULL original CV text here verbatim.
"""

def interpret(pdf_path: str, model: str = "llama3") -> CandidateProfile:
    """
    Ada Lovelace: reads a CV PDF and returns a validated CandidateProfile.
    
    Args:
        pdf_path: path to the CV PDF file
        model:    Ollama model name (default: llama3)

    Returns:
        CandidateProfile — validated Pydantic object
    """
    raw_text = extract_text(pdf_path)

    user_message = f"Parse this CV:\n\n{raw_text}"

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        format="json",              # output
        options={"temperature": 0}, # deterministic
    )

    content = response["message"]["content"].strip()

    # strip accidental markdown fences if the model adds them
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[Ada Lovelace] JSON parse error: {e}")
        print(f"[Ada Lovelace] Raw LLM output:\n{content}")
        raise

    data["raw_text"] = raw_text   # always use the original extracted text, not the LLM's copy

    try:
        return CandidateProfile.model_validate(data)
    except ValidationError as e:
        print(f"[Ada Lovelace] Validation error: {e}")
        print(f"[Ada Lovelace] Parsed data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        raise


# Testing

if __name__ == "__main__":

    start = time.time()
    for i in range(1,11):
        pdf = f"data/raw/{i:02d}_cv.pdf"

        print(f"\nParsing: {pdf}\n")

        profile = interpret(pdf)

        print(f"  Name:       {profile.name}")
        print(f"  Skills:     {[s.name for s in profile.skills]}")
        print(f"  Experience: {profile.years_experience} years")
        print(f"  Education:  {profile.education_level} in {profile.education_field}")
        print(f"  Languages:  {[(l.language, l.level) for l in profile.languages]}")
        #print(f"  raw_text:   {profile.raw_text}")

    print(f"Time taken: {time.time() - start:.2f} seconds")


    

