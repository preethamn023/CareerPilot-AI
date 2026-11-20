"""Tool 4: extract_resume_information - structured profile from resume text."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.schemas.resume import ResumeProfile
from app.services import ai_analysis, repository, rule_based
from app.services.exceptions import LLMError, LLMNotConfiguredError
from app.tools.base import register_tool

_PARAMS = {
    "type": "object",
    "properties": {
        "resume_id": {"type": "integer", "description": "ID of the stored resume to extract information from"},
    },
    "required": ["resume_id"],
}


@register_tool(
    "extract_resume_information",
    "Extract structured information (name, contact, education, skills, projects, experience, "
    "certifications, achievements) from a stored resume. Uses AI when configured, otherwise "
    "rule-based extraction. Never invents missing information.",
    _PARAMS,
)
def extract_resume_information(db: Session, resume_id: int) -> ResumeProfile:
    resume = repository.get_resume(db, resume_id)

    existing = repository.resume_profile(resume)
    if existing is not None:
        return existing

    try:
        profile = ai_analysis.ai_extract_resume_profile(resume.raw_text)
    except (LLMNotConfiguredError, LLMError):
        profile = rule_based.rule_based_resume_profile(resume.raw_text)

    repository.set_resume_profile(db, resume, profile)
    return profile
