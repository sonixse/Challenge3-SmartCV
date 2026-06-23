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

# Language level normalization: handles slash/range formats (e.g. "Native/B2", "B1-B2")
# and LinkedIn-style labels (English and Spanish).
_CEFR_ORDER = ["C2", "C1", "B2", "B1", "A2", "A1"]  # highest first

# Ordered longest-first so "full professional" matches before "professional"
_LINKEDIN_LEVELS: list[tuple[str, str]] = [
    ("native or bilingual",          "Native"),
    ("bilingüe",                     "Native"),
    ("full professional",            "C1"),
    ("dominio profesional completo", "C1"),
    ("competencia profesional plena","C1"),
    ("professional working",         "B2"),
    ("competencia profesional",      "B2"),
    ("limited working",              "B1"),
    ("competencia laboral limitada", "B1"),
    ("elementary proficiency",       "A2"),
    ("competencia elemental",        "A2"),
]

def _normalize_language_level(raw: str | None) -> str:
    if not raw:
        return "B2"  # conservative default (matches SYSTEM_PROMPT)
    low = raw.lower()
    if re.search(r'\bnativ', low):  # native / nativo / nativa
        return "Native"
    for phrase, cefr in _LINKEDIN_LEVELS:
        if phrase in low:
            return cefr
    for level in _CEFR_ORDER:
        if level.lower() in low:
            return level
    return raw


def _normalize_skill(name: str) -> str:
    """Strip Spanish qualifiers/parentheticals and translate common Spanish tech terms."""
    low = name.lower().strip()
    if low in _SKILL_TRANSLATIONS:
        return _SKILL_TRANSLATIONS[low]
    cleaned = _SKILL_QUALIFIERS.sub("", name).strip()
    return cleaned if cleaned else name


# Deterministic language recovery — catches what the LLM misses
# Keys: lowercase name as it may appear in the CV (Spanish / Catalan / English)
# Values: canonical English name
_KNOWN_LANGUAGES: dict[str, str] = {
    # Spanish names
    "inglés": "English",    "ingles": "English",
    "español": "Spanish",   "castellano": "Spanish",
    "catalán": "Catalan",   "catalan": "Catalan",   "català": "Catalan",
    "francés": "French",    "frances": "French",
    "alemán": "German",     "aleman": "German",
    "italiano": "Italian",
    "portugués": "Portuguese", "portugues": "Portuguese",
    "ruso": "Russian",
    "chino": "Chinese",
    "árabe": "Arabic",      "arabe": "Arabic",
    "japonés": "Japanese",  "japones": "Japanese",
    "coreano": "Korean",
    "holandés": "Dutch",    "holandes": "Dutch",
    "sueco": "Swedish",
    "noruego": "Norwegian",
    "polaco": "Polish",
    "griego": "Greek",
    "turco": "Turkish",
    "hindi": "Hindi",
    "euskera": "Basque",    "vasco": "Basque",
    "gallego": "Galician",
    "valenciano": "Valencian",
    # Catalan names
    "anglès": "English",   "angles": "English",
    "rus": "Russian",
    "francès": "French",   "frances": "French",
    "alemany": "German",
    "italià": "Italian",   "italia": "Italian",
    "portuguès": "Portuguese",
    "xinès": "Chinese",
    "àrab": "Arabic",
    "japonès": "Japanese",
    # English names (for CVs written in English)
    "english": "English",  "spanish": "Spanish",  "french": "French",
    "german": "German",    "italian": "Italian",  "portuguese": "Portuguese",
    "russian": "Russian",  "chinese": "Chinese",  "arabic": "Arabic",
    "japanese": "Japanese","korean": "Korean",    "dutch": "Dutch",
    "swedish": "Swedish",  "norwegian": "Norwegian", "polish": "Polish",
    "greek": "Greek",      "turkish": "Turkish",  "basque": "Basque",
    "galician": "Galician","valencian": "Valencian",
}

_VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2", "Native"}

# Pattern built once at import time (longest key first to avoid partial matches)
_LANG_SCAN_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in sorted(_KNOWN_LANGUAGES, key=len, reverse=True)) + r')\b'
    r'([^,\n;]{0,30})',
    re.IGNORECASE,
)

def _recover_missing_languages(raw_text: str, found: list[dict]) -> list[dict]:
    """Scan raw_text for language names the LLM missed and append them."""
    seen = {d["language"].lower() for d in found}
    extra: list[dict] = []

    for m in _LANG_SCAN_RE.finditer(raw_text):
        en_name = _KNOWN_LANGUAGES[m.group(1).lower()]
        if en_name.lower() in seen:
            continue
        seen.add(en_name.lower())
        level = _normalize_language_level(m.group(2).strip())
        if level not in _VALID_LEVELS:
            level = "B2"
        extra.append({"language": en_name, "level": level})

    return found + extra


# PDF extraction

_LETTER_SPACING_THRESHOLD = 0.45  # ratio of single-char tokens that triggers collapse

def _fix_letter_spacing(text: str) -> str:
    """Collapse letter-spaced PDF text.

    Some PDFs (e.g. design-tool exports) store each character with a gap,
    so pypdf produces ' N a t i v o / B 2'. This function detects
    that pattern via the single-char token ratio and collapses it:
      - ≥2 consecutive spaces → word boundary (kept as one space)
      - single spaces between chars → removed (letters merged into words)
    CVs without this problem are returned unchanged.
    """
    tokens = text.split()
    if not tokens:
        return text
    ratio = sum(1 for t in tokens if len(t) == 1) / len(tokens)
    if ratio < _LETTER_SPACING_THRESHOLD:
        return text  # normal CV, leave untouched

    lines = []
    for line in text.split('\n'):
        if not line.strip():
            lines.append('')
            continue
        # ≥2 spaces = word separator; single spaces = letter separator → remove
        parts = re.split(r' {2,}', line)
        collapsed = ' '.join(p.replace(' ', '') for p in parts)
        # Two-column PDFs sometimes merge adjacent words: "nativoEspañol" → "nativo Español"
        collapsed = re.sub(r'([a-záéíóúüñ])([A-ZÁÉÍÓÚÜÑ])', r'\1 \2', collapsed)
        lines.append(collapsed)
    return '\n'.join(lines)


def extract_text(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    reader = PdfReader(pdf_path)
    pages  = [page.extract_text() or "" for page in reader.pages]
    raw    = "\n".join(pages).strip()
    return _fix_letter_spacing(raw)


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
- languages: always output the language name in English (e.g. "Inglés"→"English", "Ruso"→"Russian", "Francés"→"French", "Alemán"→"German", "Chino"→"Chinese", "Árabe"→"Arabic", "Italiano"→"Italian", "Portugués"→"Portuguese", "Japonés"→"Japanese", "Catalán"→"Catalan"). For the level, use CEFR (A1, A2, B1, B2, C1, C2) or "Native". Combined formats like "Nativo/B2" or "Native/B2" are valid — extract them as-is and pick the highest. If no level is stated, use "B2" as a conservative default.
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

            # normalize education_level, skill names, and language levels before Pydantic validation
            data["education_level"] = _normalize_education(data.get("education_level", ""))
            if "skills" in data:
                normalized = []
                for skill in data["skills"]:
                    if isinstance(skill, str):
                        skill = {"name": skill, "years": None}
                    skill["name"] = _normalize_skill(skill["name"])
                    normalized.append(skill)
                data["skills"] = normalized
            llm_langs = data.get("languages", [])
            for lang in llm_langs:
                lang["level"] = _normalize_language_level(lang.get("level", ""))
                # Translate Spanish/Catalan language names to English (llama3 ignores the prompt)
                name_key = lang.get("language", "").lower()
                lang["language"] = _KNOWN_LANGUAGES.get(name_key, lang.get("language", ""))
            data["languages"] = _recover_missing_languages(raw_text, llm_langs)

            # Safe fallbacks for required fields the LLM sometimes omits
            _VALID_EDU = {"Bachelor's", "Master's", "PhD", "No degree"}
            if data.get("education_level") not in _VALID_EDU:
                data["education_level"] = "No degree"
            data.setdefault("years_experience", 0)
            data.setdefault("education_field", "Unknown")
            data.setdefault("skills", [])

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

