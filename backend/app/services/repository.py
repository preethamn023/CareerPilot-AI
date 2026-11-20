"""Database access helpers shared by API routes and the agent orchestrator."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import (
    Analysis,
    InterviewQuestionRow,
    JobDescription,
    OptimizedBullet,
    Resume,
    SkillGap,
)
from app.schemas.analysis import MatchResult, SkillGapItem
from app.schemas.interview import InterviewQuestion
from app.schemas.job import JobDescriptionInfo
from app.schemas.optimization import BulletOptimization
from app.schemas.resume import ResumeProfile
from app.services.exceptions import NotFoundError


# ------------------------------------------------------------------ resumes
def create_resume(db: Session, filename: str, raw_text: str, page_count: int) -> Resume:
    resume = Resume(filename=filename, raw_text=raw_text, page_count=page_count, char_count=len(raw_text))
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def set_resume_profile(db: Session, resume: Resume, profile: ResumeProfile) -> Resume:
    resume.profile_json = profile.model_dump()
    resume.extraction_method = profile.extraction_method
    db.commit()
    db.refresh(resume)
    return resume


def get_resume(db: Session, resume_id: int) -> Resume:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise NotFoundError(f"Resume {resume_id} was not found.")
    return resume


def resume_profile(resume: Resume) -> ResumeProfile | None:
    if not resume.profile_json:
        return None
    try:
        return ResumeProfile.model_validate(resume.profile_json)
    except Exception:  # noqa: BLE001 - corrupted JSON must not crash reads
        return None


def list_resumes(db: Session, limit: int = 50) -> list[Resume]:
    return list(db.scalars(select(Resume).order_by(Resume.id.desc()).limit(limit)))


def delete_resume(db: Session, resume_id: int) -> None:
    resume = get_resume(db, resume_id)
    db.delete(resume)
    db.commit()


# --------------------------------------------------------------------- jobs
def create_job(
    db: Session,
    source: str,
    url: str | None,
    title: str | None,
    raw_text: str,
    info: JobDescriptionInfo,
) -> JobDescription:
    job = JobDescription(
        source=source,
        url=url,
        title=title,
        raw_text=raw_text,
        char_count=len(raw_text),
        info_json=info.model_dump(),
        extraction_method=info.extraction_method,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> JobDescription:
    job = db.get(JobDescription, job_id)
    if not job:
        raise NotFoundError(f"Job description {job_id} was not found.")
    return job


def job_info(job: JobDescription) -> JobDescriptionInfo:
    if not job.info_json:
        return JobDescriptionInfo()
    try:
        return JobDescriptionInfo.model_validate(job.info_json)
    except Exception:  # noqa: BLE001
        return JobDescriptionInfo()


def list_jobs(db: Session, limit: int = 50) -> list[JobDescription]:
    return list(db.scalars(select(JobDescription).order_by(JobDescription.id.desc()).limit(limit)))


# ---------------------------------------------------------------- analyses
def create_analysis(
    db: Session,
    resume: Resume,
    job: JobDescription,
    match: MatchResult,
    skill_gaps: list[SkillGapItem],
) -> Analysis:
    analysis = Analysis(
        resume_id=resume.id,
        job_id=job.id,
        overall_match_score=match.overall_match_score,
        technical_skill_score=match.technical_skill_score,
        education_score=match.education_score,
        experience_score=match.experience_score,
        project_relevance_score=match.project_relevance_score,
        analysis_method=match.analysis_method,
        match_json=match.model_dump(),
    )
    db.add(analysis)
    db.flush()
    for gap in skill_gaps:
        db.add(
            SkillGap(
                analysis_id=analysis.id,
                skill=gap.skill,
                importance=gap.importance,
                job_requirement_reason=gap.job_requirement_reason,
                current_resume_evidence=gap.current_resume_evidence,
                learning_approach=gap.learning_approach,
                suggested_project=gap.suggested_project,
                estimated_learning_duration=gap.estimated_learning_duration,
            )
        )
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis(db: Session, analysis_id: int) -> Analysis:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise NotFoundError(f"Analysis {analysis_id} was not found.")
    return analysis


def list_analyses(db: Session, limit: int = 100) -> list[Analysis]:
    return list(db.scalars(select(Analysis).order_by(Analysis.id.desc()).limit(limit)))


def analysis_match(analysis: Analysis) -> MatchResult:
    if not analysis.match_json:
        return MatchResult(overall_match_score=0, analysis_method="rule_based")
    try:
        return MatchResult.model_validate(analysis.match_json)
    except Exception:  # noqa: BLE001
        return MatchResult(overall_match_score=0, analysis_method="rule_based")


def analysis_skill_gaps(analysis: Analysis) -> list[SkillGapItem]:
    return [
        SkillGapItem(
            skill=g.skill,
            importance=g.importance,  # type: ignore[arg-type]
            job_requirement_reason=g.job_requirement_reason,
            current_resume_evidence=g.current_resume_evidence,
            learning_approach=g.learning_approach,
            suggested_project=g.suggested_project,
            estimated_learning_duration=g.estimated_learning_duration,
        )
        for g in analysis.skill_gaps
    ]


def delete_analysis(db: Session, analysis_id: int) -> None:
    analysis = get_analysis(db, analysis_id)
    db.delete(analysis)
    db.commit()


# ------------------------------------------------------------ optimizations
def save_optimizations(
    db: Session,
    resume_id: int,
    analysis_id: int | None,
    bullets: list[BulletOptimization],
) -> list[OptimizedBullet]:
    rows: list[OptimizedBullet] = []
    for bullet in bullets:
        row = OptimizedBullet(
            analysis_id=analysis_id,
            resume_id=resume_id,
            section=bullet.section,
            original_bullet=bullet.original_bullet,
            optimized_bullet=bullet.optimized_bullet,
            improvement_rationale=bullet.improvement_rationale,
            keywords_json=bullet.keywords_highlighted,
            method=bullet.method,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def list_optimizations(db: Session, analysis_id: int | None = None, resume_id: int | None = None) -> list[OptimizedBullet]:
    query = select(OptimizedBullet).order_by(OptimizedBullet.id.desc()).limit(100)
    if analysis_id is not None:
        query = query.where(OptimizedBullet.analysis_id == analysis_id)
    if resume_id is not None:
        query = query.where(OptimizedBullet.resume_id == resume_id)
    return list(db.scalars(query))


def set_optimization_selected(db: Session, optimization_id: int, selected: bool) -> OptimizedBullet:
    row = db.get(OptimizedBullet, optimization_id)
    if not row:
        raise NotFoundError(f"Optimization {optimization_id} was not found.")
    row.selected = selected
    db.commit()
    db.refresh(row)
    return row


# ------------------------------------------------------- interview questions
def save_questions(
    db: Session,
    analysis_id: int | None,
    questions: list[InterviewQuestion],
) -> list[InterviewQuestionRow]:
    rows: list[InterviewQuestionRow] = []
    for question in questions:
        row = InterviewQuestionRow(
            analysis_id=analysis_id,
            question=question.question,
            category=question.category,
            difficulty=question.difficulty,
            why_asked=question.why_asked,
            key_concepts_json=question.key_concepts,
            answer_structure=question.answer_structure,
            method=question.method,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def list_questions(db: Session, analysis_id: int | None = None) -> list[InterviewQuestionRow]:
    query = select(InterviewQuestionRow).order_by(InterviewQuestionRow.id.desc()).limit(200)
    if analysis_id is not None:
        query = query.where(InterviewQuestionRow.analysis_id == analysis_id)
    return list(db.scalars(query))
