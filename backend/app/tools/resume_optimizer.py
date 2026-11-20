"""Tool 7: optimize_resume_bullets - truthful bullet-point improvements."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.schemas.optimization import BulletOptimization
from app.schemas.resume import ResumeProfile
from app.services import ai_analysis, repository, rule_based
from app.services.exceptions import LLMError, LLMNotConfiguredError
from app.tools.base import register_tool

_PARAMS = {
    "type": "object",
    "properties": {
        "resume_id": {"type": "integer", "description": "Stored resume ID"},
        "job_id": {"type": "integer", "description": "Optional target job ID for relevance"},
    },
    "required": ["resume_id"],
}

MAX_BULLETS = 12


def collect_bullets(profile: ResumeProfile, provided: list[str] | None = None) -> list[tuple[str, str]]:
    """Gather optimizable bullet points from the profile (or an explicit list)."""
    if provided:
        return [("custom", b) for b in provided if b and b.strip()][:MAX_BULLETS]

    bullets: list[tuple[str, str]] = []
    if profile.professional_summary and 60 < len(profile.professional_summary) < 600:
        bullets.append(("summary", profile.professional_summary))
    for project in profile.projects:
        text = " - ".join(filter(None, [project.name, project.description]))
        if text and len(text) > 30:
            bullets.append(("projects", text))
    for item in profile.internships:
        text = " - ".join(filter(None, [item.role, item.organization, item.description]))
        if text and len(text) > 30:
            bullets.append(("internships", text))
    for item in profile.work_experience:
        text = " - ".join(filter(None, [item.role, item.organization, item.description]))
        if text and len(text) > 30:
            bullets.append(("work_experience", text))
    for achievement in profile.achievements:
        if achievement and len(achievement) > 25:
            bullets.append(("achievements", achievement))
    return bullets[:MAX_BULLETS]


def build_optimizations(
    db: Session,
    resume_id: int,
    job_id: int | None,
    provided_bullets: list[str] | None = None,
) -> tuple[list[BulletOptimization], str | None]:
    resume = repository.get_resume(db, resume_id)
    profile = repository.resume_profile(resume)
    if profile is None:
        from app.tools.resume_extractor import extract_resume_information

        profile = extract_resume_information(db=db, resume_id=resume_id)

    bullets = collect_bullets(profile, provided_bullets)
    if not bullets:
        return [], "No suitable bullet points were found in this resume to optimize."

    job_keywords: list[str] = []
    job_role: str | None = None
    if job_id:
        job = repository.get_job(db, job_id)
        info = repository.job_info(job)
        job_keywords = info.required_skills + info.preferred_skills
        job_role = info.role

    note = None
    try:
        result = ai_analysis.ai_optimize_bullets(bullets, job_keywords, job_role)
        if not result:
            result = rule_based.rule_based_optimize_bullets(bullets, job_keywords)
            note = "Generated with rule-based optimization (AI returned no usable output)."
    except (LLMNotConfiguredError, LLMError):
        result = rule_based.rule_based_optimize_bullets(bullets, job_keywords)
        note = "Generated with rule-based optimization (no AI provider configured)."
    return result, note


@register_tool(
    "optimize_resume_bullets",
    "Generate improved versions of the resume's bullet points: professional wording, action "
    "verbs, clearer achievements and highlighted technologies - strictly preserving factual "
    "accuracy (never invents projects, metrics or experience). Optionally targets a stored job.",
    _PARAMS,
)
def optimize_resume_bullets(db: Session, resume_id: int, job_id: int | None = None) -> dict[str, Any]:
    bullets, note = build_optimizations(db, resume_id, job_id)
    return {"optimizations": [b.model_dump() for b in bullets], "note": note}
