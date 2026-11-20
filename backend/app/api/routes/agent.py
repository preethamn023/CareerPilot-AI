"""API routes: conversational agent (LLM tool-calling loop)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.orchestrator import orchestrator
from app.models.database import get_db
from app.services.exceptions import CareerPilotError, LLMNotConfiguredError
from app.services.llm_service import llm_service

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    message: str
    resume_id: int | None = None
    job_id: int | None = None


class AgentStepOut(BaseModel):
    tool: str
    arguments: dict
    ok: bool
    summary: str


class AgentChatResponse(BaseModel):
    reply: str
    steps: list[AgentStepOut]
    provider: str


@router.get("/status", summary="Which AI engine is active and which tools are registered")
def agent_status() -> dict:
    from app.tools import tool_specs

    return {
        "ai": llm_service.provider_status(),
        "tools": [spec["name"] for spec in tool_specs()],
    }


@router.post("/chat", response_model=AgentChatResponse, summary="Chat with the CareerPilot agent")
def agent_chat(payload: AgentChatRequest, db: Session = Depends(get_db)) -> AgentChatResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail={"message": "message is required", "code": "invalid_input"})
    try:
        result = orchestrator.chat(db, payload.message, payload.resume_id, payload.job_id)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail={"message": exc.message, "code": exc.code}) from exc
    except CareerPilotError as exc:
        raise HTTPException(status_code=422, detail={"message": exc.message, "code": exc.code}) from exc
    return AgentChatResponse(
        reply=result.reply,
        steps=[AgentStepOut(tool=s.tool, arguments=s.arguments, ok=s.ok, summary=s.summary) for s in result.steps],
        provider=result.provider,
    )
