"""API routes: Module B - job description scraping and analysis."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import orchestrator
from app.models.database import get_db
from app.schemas.job import (
    AnalyzeJobRequest,
    JobListItem,
    JobResponse,
    ScrapeRequest,
    ScrapedJob,
)
from app.services import repository, scrape_service
from app.services.exceptions import CareerPilotError

router = APIRouter(tags=["jobs"])


def _to_response(job) -> JobResponse:
    return JobResponse(
        id=job.id,
        source=job.source,
        url=job.url,
        created_at=job.created_at.isoformat(),
        extraction_method=job.extraction_method,  # type: ignore[arg-type]
        job=repository.job_info(job),
    )


@router.post(
    "/jobs/scrape",
    response_model=ScrapedJob,
    summary="Safely scrape a public job-description URL and return cleaned text (no AI)",
)
def scrape_job(payload: ScrapeRequest, db: Session = Depends(get_db)) -> ScrapedJob:
    try:
        page, cleaned = scrape_service.scrape_job_description(payload.url)
    except CareerPilotError as exc:
        raise HTTPException(status_code=422, detail={"message": exc.message, "code": exc.code}) from exc
    return ScrapedJob(
        url=page.url,
        final_url=page.final_url,
        title=cleaned.title or page.title,
        meta_description=page.meta_description,
        text=cleaned.text,
        char_count=cleaned.char_count,
    )


@router.post(
    "/jobs/analyze",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyse a job description from a URL or pasted text and store it",
)
def analyze_job(payload: AnalyzeJobRequest, db: Session = Depends(get_db)) -> JobResponse:
    if not payload.url and not payload.text:
        raise HTTPException(
            status_code=422,
            detail={"message": "Provide either a job description URL or the job description text.", "code": "missing_input"},
        )
    try:
        result = orchestrator.run_pipeline(
            "analyze_job", db, url=payload.url, text=payload.text, title=payload.title
        )
    except CareerPilotError as exc:
        raise HTTPException(status_code=422, detail={"message": exc.message, "code": exc.code}) from exc
    return _to_response(result["job"])


@router.get("/jobs", response_model=list[JobListItem], summary="List analysed jobs")
def list_jobs(db: Session = Depends(get_db)) -> list[JobListItem]:
    items = []
    for job in repository.list_jobs(db):
        info = repository.job_info(job)
        items.append(
            JobListItem(
                id=job.id,
                source=job.source,
                url=job.url,
                role=info.role,
                company=info.company,
                created_at=job.created_at.isoformat(),
            )
        )
    return items


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get one analysed job")
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    try:
        job = repository.get_job(db, job_id)
    except CareerPilotError as exc:
        raise HTTPException(status_code=404, detail={"message": exc.message, "code": exc.code}) from exc
    return _to_response(job)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a job and its analyses")
def delete_job(job_id: int, db: Session = Depends(get_db)) -> None:
    try:
        job = repository.get_job(db, job_id)
    except CareerPilotError as exc:
        raise HTTPException(status_code=404, detail={"message": exc.message, "code": exc.code}) from exc
    db.delete(job)
    db.commit()
