"""Tool 8: generate_interview_questions - personalised mock interview."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.schemas.interview import ALL_CATEGORIES, InterviewQuestion
from app.services import ai_analysis, repository, rule_based
from app.services.exceptions import LLMError, LLMNotConfiguredError
from app.tools.base import register_tool

_PARAMS = {
    "type": "object",
    "properties": {
        "resume_id": {"type": "integer", "description": "Stored resume ID"},
        "job_id": {"type": "integer", "description": "Stored job description ID"},
        "categories": {
            "type": "array",
            "items": {"type": "string", "enum": ALL_CATEGORIES},
            "description": "Question categories to generate",
        },
        "questions_per_category": {"type": "integer", "description": "Minimum questions per category (default 5)"},
    },
    "required": ["resume_id", "job_id"],
}


def build_questions(
    db: Session,
    resume_id: int,
    job_id: int | None,
    categories: list[str],
    per_category: int,
) -> tuple[list[InterviewQuestion], str | None]:
    resume = repository.get_resume(db, resume_id)
    profile = repository.resume_profile(resume)
    if profile is None:
        from app.tools.resume_extractor import extract_resume_information

        profile = extract_resume_information(db=db, resume_id=resume_id)

    job_info = None
    if job_id:
        job = repository.get_job(db, job_id)
        job_info = repository.job_info(job)
    if job_info is None:
        from app.schemas.job import JobDescriptionInfo

        job_info = JobDescriptionInfo(role="general placement role")

    categories = [c for c in categories if c in ALL_CATEGORIES] or ["technical", "project", "hr"]
    per_category = max(1, min(per_category, 10))

    note = None
    try:
        questions = ai_analysis.ai_generate_interview_questions(profile, job_info, categories, per_category)
        if not questions:
            questions = rule_based.rule_based_interview_questions(profile, job_info, categories, per_category)
            note = "Generated with rule-based templates (AI returned no usable output)."
    except (LLMNotConfiguredError, LLMError):
        questions = rule_based.rule_based_interview_questions(profile, job_info, categories, per_category)
        note = "Generated with rule-based templates (no AI provider configured)."
    return questions, note


@register_tool(
    "generate_interview_questions",
    "Generate personalised interview questions grounded in the candidate's resume and the "
    "target job: technical, programming, project, HR, behavioral and scenario categories, "
    "each with difficulty, why it is asked, key concepts and a suggested answer structure.",
    _PARAMS,
)
def generate_interview_questions(
    db: Session,
    resume_id: int,
    job_id: int,
    categories: list[str] | None = None,
    questions_per_category: int = 5,
) -> dict[str, Any]:
    questions, note = build_questions(
        db,
        resume_id,
        job_id,
        categories or ["technical", "project", "hr"],
        questions_per_category,
    )
    return {"questions": [q.model_dump() for q in questions], "note": note}
