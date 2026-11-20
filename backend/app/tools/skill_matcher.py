"""Tool 5: calculate_match_score - explainable resume vs job compatibility."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.schemas.analysis import MatchResult
from app.services import ai_analysis, repository, rule_based
from app.services.exceptions import LLMError, LLMNotConfiguredError
from app.tools.base import register_tool

_PARAMS = {
    "type": "object",
    "properties": {
        "resume_id": {"type": "integer", "description": "Stored resume ID"},
        "job_id": {"type": "integer", "description": "Stored job description ID"},
    },
    "required": ["resume_id", "job_id"],
}


def build_match(resume_id: int, job_id: int, db: Session) -> MatchResult:
    """Shared matching pipeline used by the tool, routes and other tools."""
    resume = repository.get_resume(db, resume_id)
    job = repository.get_job(db, job_id)

    profile = repository.resume_profile(resume)
    if profile is None:
        from app.tools.resume_extractor import extract_resume_information

        profile = extract_resume_information(db=db, resume_id=resume_id)

    job_parsed = repository.job_info(job)
    if not job.info_json:
        # Job was stored without structured info - analyse it now.
        from app.tools.job_analyzer import analyze_job_description

        job_parsed = analyze_job_description(db=db, text=job.raw_text).job
        job.info_json = job_parsed.model_dump()
        job.extraction_method = job_parsed.extraction_method
        db.commit()
        db.refresh(job)

    # Deterministic baseline (always computed - keeps the score explainable).
    base = rule_based.rule_based_match(profile, job_parsed, resume.raw_text)

    try:
        classifications = ai_analysis.ai_classify_skills(profile, job_parsed, resume.raw_text)
        judgement = ai_analysis.ai_judge_dimensions(profile, job_parsed, resume.raw_text)
        merged = ai_analysis.merge_ai_match(base, classifications, judgement, job_parsed)
        return merged
    except (LLMNotConfiguredError, LLMError):
        return base


@register_tool(
    "calculate_match_score",
    "Compare a stored resume against a stored job description and return an explainable "
    "compatibility report: overall score 0-100, technical/education/experience/project "
    "sub-scores, matched / partially matched / missing skills with evidence, and "
    "recommendations. Scores use a fixed weighted methodology - NOT an employer ATS score.",
    _PARAMS,
)
def calculate_match_score(db: Session, resume_id: int, job_id: int) -> MatchResult:
    return build_match(resume_id, job_id, db)
