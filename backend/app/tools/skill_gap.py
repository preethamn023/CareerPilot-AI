"""Tool 6: identify_skill_gaps - actionable learning plan for missing skills."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.schemas.analysis import MatchResult, SkillGapItem
from app.services import ai_analysis, repository, rule_based
from app.services.exceptions import LLMError, LLMNotConfiguredError
from app.models.entities import Analysis
from app.tools.base import register_tool

_PARAMS = {
    "type": "object",
    "properties": {
        "resume_id": {"type": "integer", "description": "Stored resume ID"},
        "job_id": {"type": "integer", "description": "Stored job description ID"},
    },
    "required": ["resume_id", "job_id"],
}


def _latest_match(db: Session, resume_id: int, job_id: int) -> MatchResult:
    """Reuse the newest stored analysis for this pair, or compute a fresh one."""
    analysis = db.scalars(
        select(Analysis)
        .where(Analysis.resume_id == resume_id, Analysis.job_id == job_id)
        .order_by(Analysis.id.desc())
        .limit(1)
    ).first()
    if analysis and analysis.match_json:
        return repository.analysis_match(analysis)
    from app.tools.skill_matcher import build_match

    return build_match(resume_id, job_id, db)


def build_skill_gaps(db: Session, resume_id: int, job_id: int) -> tuple[MatchResult, list[SkillGapItem]]:
    match = _latest_match(db, resume_id, job_id)
    job = repository.get_job(db, job_id)
    job_parsed = repository.job_info(job)
    try:
        gaps = ai_analysis.ai_skill_gaps(match, job_parsed)
        if not gaps:
            gaps = rule_based.rule_based_skill_gaps(match, job_parsed)
    except (LLMNotConfiguredError, LLMError):
        gaps = rule_based.rule_based_skill_gaps(match, job_parsed)
    return match, gaps


@register_tool(
    "identify_skill_gaps",
    "Identify the skills the candidate should learn or strengthen for the target job and "
    "return an actionable plan per skill: importance, why the job needs it, current resume "
    "evidence, learning approach, suggested project and estimated duration.",
    _PARAMS,
)
def identify_skill_gaps(db: Session, resume_id: int, job_id: int) -> dict[str, Any]:
    match, gaps = build_skill_gaps(db, resume_id, job_id)
    return {
        "overall_match_score": match.overall_match_score,
        "skill_gaps": [g.model_dump() for g in gaps],
    }
