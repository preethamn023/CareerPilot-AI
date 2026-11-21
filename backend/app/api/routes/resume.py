"""API routes: Module A - resume upload and management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import orchestrator
from app.models.database import get_db
from app.schemas.resume import ResumeListItem, ResumeResponse
from app.services import repository
from app.services.exceptions import CareerPilotError

router = APIRouter(prefix="/resume", tags=["resume"])


def _to_response(resume) -> ResumeResponse:
    profile = repository.resume_profile(resume)
    return ResumeResponse(
        id=resume.id,
        filename=resume.filename,
        char_count=resume.char_count,
        page_count=resume.page_count,
        extraction_method=resume.extraction_method,  # type: ignore[arg-type]
        profile=profile,
        created_at=resume.created_at.isoformat(),
        updated_at=resume.updated_at.isoformat(),
    )


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF resume, extract text and analyse its structure",
)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ResumeResponse:
    content = await file.read()
    try:
        result = orchestrator.run_pipeline(
            "analyze_resume", db, filename=file.filename or "resume.pdf", content=content
        )
    except CareerPilotError as exc:
        raise HTTPException(status_code=422, detail={"message": exc.message, "code": exc.code}) from exc
    return _to_response(result["resume"])


@router.get("", response_model=list[ResumeListItem], summary="List uploaded resumes")
def list_resumes(db: Session = Depends(get_db)) -> list[ResumeListItem]:
    return [
        ResumeListItem(
            id=r.id,
            filename=r.filename,
            full_name=(repository.resume_profile(r).full_name if repository.resume_profile(r) else None),
            char_count=r.char_count,
            created_at=r.created_at.isoformat(),
        )
        for r in repository.list_resumes(db)
    ]


@router.get("/{resume_id}", response_model=ResumeResponse, summary="Get one resume with its parsed profile")
def get_resume(resume_id: int, db: Session = Depends(get_db)) -> ResumeResponse:
    try:
        resume = repository.get_resume(db, resume_id)
    except CareerPilotError as exc:
        raise HTTPException(status_code=404, detail={"message": exc.message, "code": exc.code}) from exc
    return _to_response(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, summary="Delete a resume and its analyses")
def delete_resume(resume_id: int, db: Session = Depends(get_db)) -> None:
    try:
        repository.delete_resume(db, resume_id)
    except CareerPilotError as exc:
        raise HTTPException(status_code=404, detail={"message": exc.message, "code": exc.code}) from exc
