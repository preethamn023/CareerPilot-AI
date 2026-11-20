"""Schemas for Module F - AI Mock Interview Agent."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import Difficulty, ExtractionMethod

QuestionCategory = Literal[
    "technical",
    "programming",
    "project",
    "hr",
    "behavioral",
    "scenario",
]

ALL_CATEGORIES: list[str] = [
    "technical",
    "programming",
    "project",
    "hr",
    "behavioral",
    "scenario",
]


class InterviewQuestion(BaseModel):
    question: str
    category: QuestionCategory
    difficulty: Difficulty = "medium"
    why_asked: str | None = None
    key_concepts: list[str] = Field(default_factory=list)
    answer_structure: str | None = None
    method: ExtractionMethod = "rule_based"


class InterviewQuestionList(BaseModel):
    questions: list[InterviewQuestion] = Field(default_factory=list)


class GenerateInterviewRequest(BaseModel):
    resume_id: int
    job_id: int | None = None
    analysis_id: int | None = None
    categories: list[str] = Field(default_factory=lambda: ["technical", "project", "hr"])
    questions_per_category: int = 5


class StoredInterviewQuestion(InterviewQuestion):
    id: int


class GenerateInterviewResponse(BaseModel):
    questions: list[StoredInterviewQuestion]
    method: ExtractionMethod
    note: str | None = None


class EvaluateAnswerRequest(BaseModel):
    question: str
    answer: str
    resume_id: int | None = None
    job_id: int | None = None
    question_id: int | None = None


class AnswerEvaluation(BaseModel):
    """Structured feedback on a candidate's interview answer."""

    overall_feedback: str
    relevance_score: int = Field(ge=0, le=100)
    clarity_score: int = Field(ge=0, le=100)
    technical_accuracy_score: int = Field(ge=0, le=100)
    completeness_score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    suggested_answer_outline: str | None = None
    disclaimer: str = (
        "AI feedback is for practice purposes only and represents an "
        "automated opinion, not an employer's judgement."
    )


class EvaluateAnswerResponse(BaseModel):
    evaluation: AnswerEvaluation
    method: ExtractionMethod
