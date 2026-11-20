"""API routes: Modules C+D - match analysis and skill gap reports."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import orchestrator
from app.models.database import get_db
from app.schemas.analysis import AnalysisReport, MatchRequest
from app.services import repository
from app.services.exceptions import CareerPilotError

router = APIRouter(tags=["analysis"])


@router.post(
    "/analysis/match",
    response_model=AnalysisReport,
    status_code=status.HTTP_201_CREATED,
    summary="Compare a resume with a job description (match score, skills, gaps)",
)
def run_match(payload: MatchRequest, db: Session = Depends(get_db)) -> AnalysisReport:
    try:
        result = orchestrator.run_pipeline(
            "match", db, resume_id=payload.resume_id, job_id=payload.job_id
        )
    except CareerPilotError as exc:
        code = 404 if exc.code == "not_found" else 422
        raise HTTPException(status_code=code, detail={"message": exc.message, "code": exc.code}) from exc
    return build_report(db, result["analysis"])


@router.get("/analysis/{analysis_id}", response_model=AnalysisReport, summary="Get a stored analysis report")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisReport:
    try:
        analysis = repository.get_analysis(db, analysis_id)
    except CareerPilotError as exc:
        raise HTTPException(status_code=404, detail={"message": exc.message, "code": exc.code}) from exc
    return build_report(db, analysis)


def build_report(db, analysis) -> AnalysisReport:
    job = repository.get_job(db, analysis.job_id)
    info = repository.job_info(job)
    return AnalysisReport(
        analysis_id=analysis.id,
        resume_id=analysis.resume_id,
        job_id=analysis.job_id,
        created_at=analysis.created_at.isoformat(),
        job_role=info.role,
        company=info.company,
        match=repository.analysis_match(analysis),
        skill_gaps=repository.analysis_skill_gaps(analysis),
    )
