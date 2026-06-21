"""Pydantic data contracts for the CV extractor agent.

Camps alineats amb l'esquema de `ofertes.json` (skills, tools,
years_experience, highest_degree) perquè el matching CV<->oferta
sigui directe sense capes de traducció.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Skill(BaseModel):
    """Habilitat o eina, amb categoria/propòsit (analysis, querying, ...)."""
    name: str
    purpose: str


class ExperienceEntry(BaseModel):
    """Una entrada de l'experiència professional."""
    role: str = Field(..., description="Càrrec o posició")
    company: str = Field(..., description="Empresa / organització")
    duration: str = Field(..., description="Durada (ex: '2020-2023', '2 anys')")
    description: Optional[str] = None


class EducationEntry(BaseModel):
    """Una entrada de formació acadèmica."""
    degree: str = Field(..., description="Títol obtingut")
    institution: str = Field(..., description="Centre / universitat")
    year: Optional[str] = Field(None, description="Any o rang d'anys")


class CV(BaseModel):
    """CV estructurat — alineat amb l'esquema d'ofertes per a matching directe."""

    # Camps compartits amb ofertes.json
    skills: List[Skill] = Field(default_factory=list)
    tools: List[Skill] = Field(default_factory=list)
    years_experience: int = 0
    highest_degree: str = ""

    # Camps addicionals propis del CV
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
