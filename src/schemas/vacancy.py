from pydantic import BaseModel

class ToolItem(BaseModel):
    name: str
    purpose: str

class SkillItem(BaseModel):
    name: str
    purpose: str
    count: int | None = None

class Vacancy(BaseModel):
    id: int
    job_title: str
    sector: str
    years_experience: int
    has_internship: bool
    highest_degree: str
    tools: list[ToolItem]
    skills: list[SkillItem]