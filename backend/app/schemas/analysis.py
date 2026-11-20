"""Schemas for Module C (matching) and Module D (skill gap analysis)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ExtractionMethod, Importance, MatchType


class MatchedSkill(BaseModel):
    skill: str
    evidence: str | None = None
    match_type: MatchType = "demonstrated"


class PartiallyMatchedSkill(BaseModel):
    skill: str
    evidence: str | None = None
    match_type: MatchType = "partial"
    reason_partial: str | None = None


class MissingSkill(BaseModel):
    skill: str
    importance: Importance = "medium"
    reason: str | None = None


class ScoreDimension(BaseModel):
    name: str
    score: int
    weight: float
    explanation: str


class MatchResult(BaseModel):
    """Explainable resume-vs-job compatibility report.

    NOTE: this is an explainable heuristic + AI assessment for preparation
    purposes only. It is NOT an employer ATS score and is no guarantee of
    selection."""

    overall_match_score: int = Field(ge=0, le=100)
    technical_skill_score: int = Field(ge=0, le=100)
    education_score: int = Field(ge=0, le=100)
    experience_score: int = Field(ge=0, le=100)
    project_relevance_score: int = Field(ge=0, le=100)
    matched_skills: list[MatchedSkill] = Field(default_factory=list)
    partially_matched_skills: list[PartiallyMatchedSkill] = Field(default_factory=list)
    missing_skills: list[MissingSkill] = Field(default_factory=list)
    resume_evidence: list[str] = Field(default_factory=list)
    unmet_requirements: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    score_breakdown: list[ScoreDimension] = Field(default_factory=list)
    score_explanation: str = ""
    analysis_method: ExtractionMethod = "rule_based"
    disclaimer: str = (
        "This score is an explainable AI-assisted estimate for preparation "
        "purposes only. It is not an employer ATS score and does not guarantee "
        "or predict selection."
    )

    @field_validator(
        "overall_match_score",
        "technical_skill_score",
        "education_score",
        "experience_score",
        "project_relevance_score",
        mode="before",
    )
    @classmethod
    def _clamp_scores(cls, v: object) -> int:
        try:
            return max(0, min(100, int(round(float(v)))))  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError("score must be numeric") from exc


class SkillGapItem(BaseModel):
    """Module D - one actionable learning recommendation for a missing skill."""

    skill: str
    importance: Importance = "medium"
    job_requirement_reason: str | None = None
    current_resume_evidence: str | None = None
    learning_approach: str | None = None
    suggested_project: str | None = None
    estimated_learning_duration: str | None = None


class MatchRequest(BaseModel):
    resume_id: int
    job_id: int


class SkillGapResponse(BaseModel):
    skill_gaps: list[SkillGapItem]


class AnalysisReport(BaseModel):
    """Full stored analysis report returned by GET /api/analysis/{id}."""

    analysis_id: int
    resume_id: int
    job_id: int
    created_at: str
    job_role: str | None = None
    company: str | None = None
    match: MatchResult
    skill_gaps: list[SkillGapItem] = Field(default_factory=list)


class HistoryItem(BaseModel):
    analysis_id: int
    resume_id: int
    job_id: int
    job_role: str | None = None
    company: str | None = None
    overall_match_score: int
    analysis_method: ExtractionMethod
    created_at: str


class AIJudgement(BaseModel):
    """Internal schema used when the LLM judges the non-skill dimensions."""

    education_score: int = Field(ge=0, le=100)
    education_reasoning: str = ""
    experience_score: int = Field(ge=0, le=100)
    experience_reasoning: str = ""
    project_relevance_score: int = Field(ge=0, le=100)
    project_relevance_reasoning: str = ""
    resume_evidence: list[str] = Field(default_factory=list)
    unmet_requirements: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


SkillStatus = Literal["demonstrated", "partial", "listed", "missing"]


class SkillClassification(BaseModel):
    """Internal schema for one skill judged by the LLM."""

    skill: str
    status: SkillStatus = "missing"
    evidence: str | None = None
    importance: Importance = "medium"
    reason: str | None = None


class SkillClassificationList(BaseModel):
    """Internal wrapper so the LLM returns all classifications in one call."""

    classifications: list[SkillClassification] = Field(default_factory=list)
