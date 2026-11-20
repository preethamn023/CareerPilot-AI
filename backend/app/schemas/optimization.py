"""Schemas for Module E - AI Resume Optimizer."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ExtractionMethod

BulletSection = Literal["summary", "education", "skills", "projects", "internships", "work_experience", "certifications", "achievements"]


class BulletOptimization(BaseModel):
    """One improvement suggestion. Optimized text may ONLY rephrase
    information that exists in the original bullet - never add invented
    facts, metrics, or achievements."""

    section: str = "projects"
    original_bullet: str
    optimized_bullet: str
    improvement_rationale: str
    keywords_highlighted: list[str] = Field(default_factory=list)
    method: ExtractionMethod = "rule_based"


class OptimizeRequest(BaseModel):
    resume_id: int
    job_id: int | None = None
    analysis_id: int | None = None
    bullets: list[str] | None = None  # optional explicit list to optimize


class OptimizationSelectionRequest(BaseModel):
    selected: bool


class OptimizeResponse(BaseModel):
    optimizations: list[BulletOptimization]
    method: ExtractionMethod
    note: str | None = None
