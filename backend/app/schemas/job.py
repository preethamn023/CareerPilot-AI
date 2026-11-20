"""Schemas for Module B - Job Description Analyzer."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ExtractionMethod


class JobDescriptionInfo(BaseModel):
    """Structured representation of a job posting."""

    company: str | None = None
    role: str | None = None
    location: str | None = None
    employment_type: str | None = None
    experience_requirements: str | None = None
    education_requirements: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    salary_range: str | None = None
    extraction_method: ExtractionMethod = "rule_based"


class ScrapedJob(BaseModel):
    """Result of the deterministic web scraping step (no AI involved)."""

    url: str
    final_url: str
    title: str | None = None
    meta_description: str | None = None
    text: str
    char_count: int


class JobResponse(BaseModel):
    id: int
    source: str
    url: str | None = None
    created_at: str
    extraction_method: ExtractionMethod
    job: JobDescriptionInfo


class JobListItem(BaseModel):
    id: int
    source: str
    url: str | None = None
    role: str | None = None
    company: str | None = None
    created_at: str


class AnalyzeJobRequest(BaseModel):
    url: str | None = None
    text: str | None = None
    title: str | None = None

    model_config = {"protected_namespaces": ()}


class ScrapeRequest(BaseModel):
    url: str
