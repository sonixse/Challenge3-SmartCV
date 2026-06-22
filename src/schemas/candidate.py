from pydantic import BaseModel
from typing import Optional, Literal

class CandidateSkill(BaseModel):
    name: str                       # "Python", "Databases"
    years: Optional[int] = None     # years of hands-on experience, if inferable

class CandidateLanguage(BaseModel):
    language: str                   # "English", "Spanish"
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2", "Native"]  # CEFR or Native

class CandidateProfile(BaseModel):
    name: str                       # Candidate's name (for display only)
    location: Optional[str] = None  # City/country as stated in the CV
    contact: Optional[str] = None   # Email (preferred) or phone number

    # Used by Alan Turing:
    # each skill name is embedded and compared against vacancy skills
    skills: list[CandidateSkill]

    # Used by Marie Curie: 
    # compared against vacancy's years_experience requirement
    years_experience: int

    """
    # TODO: add experience: list[ExperienceEntry] (role/company/duration per job)
    # when a sector-relevance agent is built. extractor/models.py has a prior version.

    """

    # compared against vacancy's highest_degree requirement
    education_level: Literal["Bachelor's", "Master's", "PhD", "No degree"]
    education_field: str            # "Computer Science", "Data Engineering"

    # operational constraint, not semantic
    languages: list[CandidateLanguage]

    # Used by Hedy Lamarr: full cv text (raw context) to find implicit evidence for grey-zone skills
    raw_text: str

if __name__ == "__main__":
    sample = CandidateProfile(
        name="Speedy Gonzalez",
        skills=[
            CandidateSkill(name="AWS", years=5),
            CandidateSkill(name="Django", years=1),
            CandidateSkill(name="Java", years=20)
        ],
        years_experience=12,
        education_level="Master's",
        education_field="Computer Science",
        languages=[
            CandidateLanguage(language="Spanish",level="Native"),
            CandidateLanguage(language="Portuguese",level="B2")
        ],
        raw_text="Hola, soy Speedy y he trabajado en programacion muchos años. "  
    )

    print(f"  Name:       {sample.name}")
    print(f"  Skills:     {[s.name for s in sample.skills]}")
    print(f"  Experience: {sample.years_experience} years")
    print(f"  Education:  {sample.education_level} in {sample.education_field}")
    print(f"  Languages:  {[(l.language, l.level) for l in sample.languages]}")
    print(f"  raw_text:   {sample.raw_text}")
