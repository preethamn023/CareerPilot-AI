"""Schemas for Module A - Resume Intelligence."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ExtractionMethod


class Education(BaseModel):
    degree: str | None = None
    institution: str | None = None
    year: str | None = None
    score: str | None = None  # CGPA / percentage as written in the resume


class Project(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    key_contributions: list[str] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    role: str | None = None
    organization: str | None = None
    duration: str | None = None
    description: str | None = None


class ResumeProfile(BaseModel):
    """Structured representation of a resume. Missing information stays
    None / empty - the AI must never fabricate content."""

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    professional_summary: str | None = None
    education: list[Education] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools_and_technologies: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    internships: list[ExperienceItem] = Field(default_factory=list)
    work_experience: list[ExperienceItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    extraction_method: ExtractionMethod = "rule_based"


class ResumeResponse(BaseModel):
    id: int
    filename: str
    char_count: int
    page_count: int
    extraction_method: ExtractionMethod
    profile: ResumeProfile | None = None
    created_at: str
    updated_at: str


class ResumeListItem(BaseModel):
    id: int
    filename: str
    full_name: str | None = None
    char_count: int
    created_at: str
