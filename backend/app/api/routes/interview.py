"""API routes: Module F - mock interview generation and answer evaluation."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import orchestrator
from app.config import settings
from app.models.database import get_db
from app.schemas.interview import (
    ALL_CATEGORIES,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    GenerateInterviewRequest,
    GenerateInterviewResponse,
    StoredInterviewQuestion,
)
from app.services import repository
from app.services.exceptions import CareerPilotError, LLMNotConfiguredError

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post(
    "/generate",
    response_model=GenerateInterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate personalised interview questions from a resume and job",
)
def generate_questions(payload: GenerateInterviewRequest, db: Session = Depends(get_db)) -> GenerateInterviewResponse:
    categories = [c for c in payload.categories if c in ALL_CATEGORIES]
    if not categories:
        raise HTTPException(
            status_code=422,
            detail={"message": f"categories must be a subset of {ALL_CATEGORIES}", "code": "invalid_categories"},
        )
    per_category = min(
        max(1, payload.questions_per_category),
        settings.max_questions_per_category,
    )
    try:
        result = orchestrator.run_pipeline(
            "interview",
            db,
            resume_id=payload.resume_id,
            job_id=payload.job_id,
            analysis_id=payload.analysis_id,
            categories=categories,
            per_category=per_category,
        )
    except CareerPilotError as exc:
        code = 404 if exc.code == "not_found" else 422
        raise HTTPException(status_code=code, detail={"message": exc.message, "code": exc.code}) from exc

    questions = [
        StoredInterviewQuestion(
            id=row.id,
            question=row.question,
            category=row.category,  # type: ignore[arg-type]
            difficulty=row.difficulty,  # type: ignore[arg-type]
            why_asked=row.why_asked,
            key_concepts=row.key_concepts_json or [],
            answer_structure=row.answer_structure,
            method=row.method,  # type: ignore[arg-type]
        )
        for row in result["rows"]
    ]
    return GenerateInterviewResponse(
        questions=questions,
        method=questions[0].method if questions else "rule_based",
        note=result.get("note"),
    )


@router.get("", summary="List stored interview questions (optionally for one analysis)")
def list_questions(analysis_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": row.id,
            "analysis_id": row.analysis_id,
            "question": row.question,
            "category": row.category,
            "difficulty": row.difficulty,
            "why_asked": row.why_asked,
            "key_concepts": row.key_concepts_json or [],
            "answer_structure": row.answer_structure,
            "method": row.method,
            "created_at": row.created_at.isoformat(),
        }
        for row in repository.list_questions(db, analysis_id=analysis_id)
    ]


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a stored question",
)
def delete_question(question_id: int, db: Session = Depends(get_db)) -> None:
    row = db.get(__import__("app.models.entities", fromlist=["InterviewQuestionRow"]).InterviewQuestionRow, question_id)
    if not row:
        raise HTTPException(status_code=404, detail={"message": "Question not found.", "code": "not_found"})
    db.delete(row)
    db.commit()


@router.post(
    "/evaluate",
    response_model=EvaluateAnswerResponse,
    summary="Evaluate a practice answer (requires an AI provider)",
)
def evaluate_answer(payload: EvaluateAnswerRequest, db: Session = Depends(get_db)) -> EvaluateAnswerResponse:
    try:
        result = orchestrator.run_pipeline(
            "evaluate_answer",
            db,
            question=payload.question,
            answer=payload.answer,
            resume_id=payload.resume_id,
            job_id=payload.job_id,
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "code": "llm_not_configured",
            },
        ) from exc
    except CareerPilotError as exc:
        code = 404 if exc.code == "not_found" else 422
        raise HTTPException(status_code=code, detail={"message": exc.message, "code": exc.code}) from exc

    from app.services.llm_service import llm_service

    provider = llm_service.provider_status()["provider"]
    return EvaluateAnswerResponse(
        evaluation=result["evaluation"],
        method="gemini" if provider == "gemini" else "glm_bridge",
    )
