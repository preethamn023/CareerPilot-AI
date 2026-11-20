"""API routes: analysis history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.analysis import HistoryItem
from app.services import repository
from app.services.exceptions import CareerPilotError

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryItem], summary="List previous analyses (newest first)")
def list_history(db: Session = Depends(get_db)) -> list[HistoryItem]:
    items: list[HistoryItem] = []
    for analysis in repository.list_analyses(db):
        job = repository.get_job(db, analysis.job_id)
        info = repository.job_info(job)
        items.append(
            HistoryItem(
                analysis_id=analysis.id,
                resume_id=analysis.resume_id,
                job_id=analysis.job_id,
                job_role=info.role,
                company=info.company,
                overall_match_score=analysis.overall_match_score,
                analysis_method=analysis.analysis_method,  # type: ignore[arg-type]
                created_at=analysis.created_at.isoformat(),
            )
        )
    return items


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a stored analysis (with its skill gaps, optimizations and questions)",
)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        repository.delete_analysis(db, analysis_id)
    except CareerPilotError as exc:
        raise HTTPException(status_code=404, detail={"message": exc.message, "code": exc.code}) from exc
    return {"message": f"Analysis {analysis_id} deleted."}
