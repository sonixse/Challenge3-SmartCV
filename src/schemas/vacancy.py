from pydantic import BaseModel, model_validator
from typing import Literal

class RequiredLanguage(BaseModel):
    language: str
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2", "Native"]

class ToolItem(BaseModel):
    name: str
    purpose: str

class SkillItem(BaseModel):
    name: str
    purpose: str
    count: int | None = None

# Normalize Spanish degree names to canonical English values
_DEGREE_KEYWORDS = [
    ("Master's",   ("master", "máster", "msc", "postgrado")),
    ("PhD",        ("phd", "ph.d", "doctor", "doctorado")),
    ("Bachelor's", ("bachelor", "grado", "licenci", "bsc", "degree", "grad")),
    ("No degree",  ("none", "sin título", "sin titulo")),
]

def _normalize_degree(raw: str) -> str:
    s = raw.lower()
    return next((canon for canon, kws in _DEGREE_KEYWORDS if any(k in s for k in kws)), raw)

class Vacancy(BaseModel):
    id: int
    job_title: str
    sector: str
    years_experience: int
    has_internship: bool
    highest_degree: str
    tools: list[ToolItem]
    skills: list[SkillItem]
    required_languages: int = 0   # minimum number of languages required
    required_language_list: list[RequiredLanguage] = []

    @model_validator(mode="after")
    def _extract_and_normalize(self) -> "Vacancy":
        # normalize degree from Spanish
        self.highest_degree = _normalize_degree(self.highest_degree)
        # extract language count from the "languages" soft skill
        for skill in self.skills:
            if skill.name.lower() == "languages" and skill.purpose == "soft":
                self.required_languages = skill.count or 0
                break
        return self