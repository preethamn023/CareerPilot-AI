"""Shared Pydantic schemas used across modules.

Every AI-generated structure in CareerPilot AI is validated against one of
these schemas before it is persisted or returned to the frontend.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExtractionMethod = Literal["gemini", "glm_bridge", "rule_based"]
Importance = Literal["high", "medium", "low"]
Difficulty = Literal["easy", "medium", "hard"]
MatchType = Literal["demonstrated", "partial", "listed"]

STRICT = ConfigDict(extra="forbid")


class OkResponse(BaseModel):
    ok: bool = True
    message: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
    ai_provider: str
    ai_configured: bool
    ai_model: str | None = None
    database: str = "connected"
    timestamp: str
