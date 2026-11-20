"""Tool 3: analyze_job_description - structured job info from raw text."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.schemas.job import JobDescriptionInfo
from app.services import ai_analysis, rule_based
from app.services.exceptions import LLMError, LLMNotConfiguredError
from app.services.llm_service import llm_service
from app.tools.base import register_tool

_PARAMS = {
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "Raw job description text to analyse"},
    },
    "required": ["text"],
}


class AnalyzedJob(BaseModel):
    job: JobDescriptionInfo
    note: str | None = None


@register_tool(
    "analyze_job_description",
    "Analyse raw job-description text and extract structured information: company, role, "
    "experience and education requirements, required/preferred skills, responsibilities "
    "and qualifications. Uses AI when configured, otherwise rule-based extraction.",
    _PARAMS,
)
def analyze_job_description(db: Session, text: str) -> AnalyzedJob:
    text = (text or "").strip()
    if len(text) < 80:
        raise ValueError("The job description text is too short to analyse (need at least 80 characters).")

    note = None
    try:
        info = ai_analysis.ai_analyze_job_description(text)
    except (LLMNotConfiguredError, LLMError):
        info = rule_based.rule_based_job_info(text)
        note = "Analysed with rule-based extraction (no AI provider configured)."
    return AnalyzedJob(job=info, note=note)


def provider_label() -> str:
    return llm_service.provider_status()["provider"]
