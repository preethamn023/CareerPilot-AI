"""API routes: Module E - resume bullet optimization."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import orchestrator
from app.models.database import get_db
from app.schemas.optimization import (
    OptimizeRequest,
    OptimizeResponse,
    OptimizationSelectionRequest,
)
from app.services import repository
from app.services.exceptions import CareerPilotError

router = APIRouter(tags=["optimizer"])


@router.post(
    "/resume/optimize",
    response_model=OptimizeResponse,
    summary="Generate improved (truthful) resume bullet points",
)
def optimize_bullets(payload: OptimizeRequest, db: Session = Depends(get_db)) -> OptimizeResponse:
    try:
        result = orchestrator.run_pipeline(
            "optimize",
            db,
            resume_id=payload.resume_id,
            job_id=payload.job_id,
            analysis_id=payload.analysis_id,
            bullets=payload.bullets,
        )
    except CareerPilotError as exc:
        code = 404 if exc.code == "not_found" else 422
        raise HTTPException(status_code=code, detail={"message": exc.message, "code": exc.code}) from exc

    optimizations = result["optimizations"]
    return OptimizeResponse(
        optimizations=optimizations,
        method=optimizations[0].method if optimizations else "rule_based",
        note=result.get("note"),
    )


@router.get(
    "/optimizations",
    summary="List stored optimization suggestions (optionally for one analysis)",
)
def list_optimizations(
    analysis_id: int | None = None,
    resume_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = repository.list_optimizations(db, analysis_id=analysis_id, resume_id=resume_id)
    return [
        {
            "id": row.id,
            "analysis_id": row.analysis_id,
            "resume_id": row.resume_id,
            "section": row.section,
            "original_bullet": row.original_bullet,
            "optimized_bullet": row.optimized_bullet,
            "improvement_rationale": row.improvement_rationale,
            "keywords_highlighted": row.keywords_json or [],
            "selected": row.selected,
            "method": row.method,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.patch(
    "/optimizations/{optimization_id}",
    summary="Select or unselect an optimization suggestion",
)
def select_optimization(
    optimization_id: int,
    payload: OptimizationSelectionRequest,
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = repository.set_optimization_selected(db, optimization_id, payload.selected)
    except CareerPilotError as exc:
        raise HTTPException(status_code=404, detail={"message": exc.message, "code": exc.code}) from exc
    return {"id": row.id, "selected": row.selected}
