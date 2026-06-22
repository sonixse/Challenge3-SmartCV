# imported by scripts/run_interpreter.py — do not run directly

import os
import json
import re
import time
import ollama
from pypdf import PdfReader
from pydantic import ValidationError

from src.schemas.candidate import CandidateProfile

MAX_RETRIES  = 3
RETRY_DELAY  = 2.0  # seconds (doubles on each retry)
MAX_WORKERS  = 2    # concurrent Ollama requests (keep low to avoid server overload)

# Maps any education_level string to a canonical Literal value via keyword matching

_EDUCATION_KEYWORDS = [
    ("Master's",   ("master", "máster", "msc", "postgrado")),
    ("PhD",        ("phd", "ph.d", "doctor", "doctorado")),
    ("Bachelor's", ("bachelor", "grado", "licenci", "bsc", "degree")),
    ("No degree",  ("none", "sin título", "sin titulo")),
]

def _normalize_education(raw: str) -> str:
    s = raw.lower()
    return next((canon for canon, kws in _EDUCATION_KEYWORDS if any(k in s for k in kws)), raw)


# Skill name normalization: strip Spanish qualifiers and translate common terms
_SKILL_QUALIFIERS = re.compile(
    r'\s*\b(b[aá]sico|b[aá]sica|avanzado|avanzada|conceptos|supervisado|supervisada'
    r'|optimizado|optimizada|para\s+\w+)\b|\s*\(.*?\)',
    re.IGNORECASE
)
_SKILL_TRANSLATIONS = {
    "machine learning supervisado": "Supervised Machine Learning",
    "aprendizaje automático":        "Machine Learning",
    "aprendizaje profundo":          "Deep Learning",
    "redes neuronales":              "Neural Networks",
    "procesamiento de lenguaje natural": "NLP",
}

def _normalize_skill(name: str) -> str:
    """Strip Spanish qualifiers/parentheticals and translate common Spanish tech terms."""
    low = name.lower().strip()
    if low in _SKILL_TRANSLATIONS:
        return _SKILL_TRANSLATIONS[low]
    cleaned = _SKILL_QUALIFIERS.sub("", name).strip()
    return cleaned if cleaned else name


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
  "location": "city, country or null",
  "contact": "email or phone or null",
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
- skills: list every technical skill, tool, framework, and methodology you can find. Always write skill names in English (e.g. "Supervised Machine Learning", not "Machine Learning supervisado"). Do NOT list soft skills (e.g. "teamwork", "communication").
- years per skill: use this inference hierarchy in order:
    1. EXPLICIT — the CV states it directly (e.g. "5 years of Python") → use that number.
    2. ROLE DURATION — the skill is used in a job whose start/end dates are given → sum those years.
    3. EDUCATION — the skill is from a degree/course with known duration → use that duration.
    4. NULL — none of the above apply → set to null. Do NOT guess or fabricate a number.
  When in doubt, underestimate rather than overestimate. Cap any single skill at years_experience.
- years_experience: total professional experience in years (0 if student/no experience). Count only paid work, not education.
- education_level: use exactly one of the four allowed values. ALWAYS in English — never translate (e.g. use "Master's", never "Máster" or "Maîtrise").
- location: city and/or country as written in the CV header. Use null if not found.
- contact: extract email address first; if absent, use phone number. Use null if neither found.
- languages: use CEFR levels (A1, A2, B1, B2, C1, C2) or "Native". If no level is stated, infer from context or use "B2" as a conservative default.
- raw_text: copy the FULL original CV text here verbatim.
"""

def interpret(pdf_path: str, model: str = "llama3") -> CandidateProfile:
    """
    Reads a CV PDF and returns a validated CandidateProfile.

    Retries up to MAX_RETRIES times on JSON parse or schema validation failures,
    with exponential backoff between attempts.

    Args:
        pdf_path: path to the CV PDF file
        model:    Ollama model name (default: llama3)

    Returns:
        CandidateProfile — validated Pydantic object

    Raises:
        json.JSONDecodeError or ValidationError after MAX_RETRIES exhausted.
    """
    raw_text = extract_text(pdf_path)
    user_message = f"Parse this CV:\n\n{raw_text}"

    last_exception: Exception | None = None
    t0 = time.time()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
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

            data = json.loads(content)
            data["raw_text"] = raw_text  # always use the original extracted text

            # normalize education_level and skill names before Pydantic validation
            data["education_level"] = _normalize_education(data.get("education_level", ""))
            if "skills" in data:
                for skill in data["skills"]:
                    skill["name"] = _normalize_skill(skill["name"])

            profile = CandidateProfile.model_validate(data)
            elapsed = time.time() - t0
            print(f"Parsed in {elapsed:.1f}s (attempt {attempt}/{MAX_RETRIES})")
            return profile

        except json.JSONDecodeError as e:
            last_exception = e
            print(f"Attempt {attempt}/{MAX_RETRIES} — JSON parse error: {e}")
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** (attempt - 1))
                print(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)

        except ValidationError as e:
            last_exception = e
            print(f"Attempt {attempt}/{MAX_RETRIES} — Schema validation error: {e}")
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** (attempt - 1))
                print(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)

        except Exception as e:
            # catches Ollama connection errors, server disconnects, timeouts
            last_exception = e
            print(f"Attempt {attempt}/{MAX_RETRIES} — Connection error: {e}")
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** attempt)  # longer backoff for server errors
                print(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)

    print(f"All {MAX_RETRIES} attempts failed for: {pdf_path}")
    assert last_exception is not None  # a successful parse would have returned
    raise last_exception


# Persistence

DEFAULT_OUTPUT_DIR = "data/processed"

def save_profile(profile: CandidateProfile, output_path: str) -> None:
    """
    Persist a CandidateProfile to disk as JSON.

    Args:
        profile:     validated CandidateProfile to save
        output_path: destination file path (will create parent dirs if needed)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, indent=2, ensure_ascii=False)

def load_profile(json_path: str) -> CandidateProfile:
    """
    Load a previously saved CandidateProfile from a JSON file.

    Args:
        json_path: path to the JSON file written by save_profile()

    Returns:
        CandidateProfile — validated Pydantic object
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CandidateProfile.model_validate(data)

