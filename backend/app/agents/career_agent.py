"""CareerAgent: the agent 'body' - validated tool execution and context.

This module never talks to the LLM directly for content generation; it:
- validates every tool argument against the tool's JSON schema,
- executes tools deterministically,
- summarises tool output for the orchestrator's conversation,
- builds the task context (active resume / job) for the LLM.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.services import repository
from app.services.exceptions import CareerPilotError
from app.services.llm_service import ToolAction, ToolSpec
from app.tools import get_tool, tool_specs


@dataclass
class AgentStep:
    tool: str
    arguments: dict[str, Any]
    ok: bool
    summary: str


class CareerAgent:
    def llm_tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(name=spec["name"], description=spec["description"], parameters=dict(spec["parameters"]))
            for spec in tool_specs()
        ]

    def execute_tool(self, db: Session, action: ToolAction) -> AgentStep:
        """Validate arguments against the tool schema, then run the tool."""
        try:
            tool = get_tool(action.tool)
        except KeyError:
            available = ", ".join(sorted(spec["name"] for spec in tool_specs()))
            return AgentStep(
                tool=action.tool,
                arguments=action.arguments,
                ok=False,
                summary=f"Unknown tool '{action.tool}'. Available tools: {available}.",
            )

        cleaned: dict[str, Any] = {}
        props = tool.parameters.get("properties", {})
        for key, value in (action.arguments or {}).items():
            if key not in props:
                continue
            if props[key].get("type") == "integer":
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    return AgentStep(
                        tool=action.tool,
                        arguments=action.arguments,
                        ok=False,
                        summary=f"Argument '{key}' must be an integer.",
                    )
            cleaned[key] = value

        for req in tool.parameters.get("required", []):
            if req not in cleaned:
                return AgentStep(
                    tool=action.tool,
                    arguments=action.arguments,
                    ok=False,
                    summary=f"Missing required argument '{req}'.",
                )

        try:
            result = tool.run(db, **cleaned)
        except CareerPilotError as exc:
            return AgentStep(tool=action.tool, arguments=cleaned, ok=False, summary=f"Tool error: {exc.message}")
        except Exception as exc:  # noqa: BLE001 - the agent must never crash the API
            return AgentStep(tool=action.tool, arguments=cleaned, ok=False, summary=f"Tool failed: {exc}")

        return AgentStep(tool=action.tool, arguments=cleaned, ok=True, summary=self.summarise(result))

    @staticmethod
    def summarise(result: Any) -> str:
        try:
            if hasattr(result, "model_dump"):
                data = result.model_dump()
            else:
                data = result
            text = json.dumps(data, ensure_ascii=False, default=str)
            return text[:3500]
        except Exception:  # noqa: BLE001
            return str(result)[:3500]

    def build_context(self, db: Session, resume_id: int | None, job_id: int | None) -> str:
        lines: list[str] = []
        if resume_id:
            try:
                resume = repository.get_resume(db, resume_id)
                profile = repository.resume_profile(resume)
                name = profile.full_name if profile else "unknown"
                lines.append(f"- Active resume_id: {resume.id} (file: {resume.filename}, candidate: {name})")
            except CareerPilotError:
                lines.append(f"- Active resume_id: {resume_id} (NOT FOUND - ask the student to re-upload)")
        else:
            resumes = repository.list_resumes(db, limit=5)
            if resumes:
                lines.append("- Available resume_ids: " + ", ".join(f"{r.id} ({r.filename})" for r in resumes))
            else:
                lines.append("- No resumes uploaded yet.")

        if job_id:
            try:
                job = repository.get_job(db, job_id)
                info = repository.job_info(job)
                lines.append(
                    f"- Active job_id: {job.id} (role: {info.role or 'unknown'}, "
                    f"company: {info.company or 'unknown'})"
                )
            except CareerPilotError:
                lines.append(f"- Active job_id: {job_id} (NOT FOUND)")
        else:
            jobs = repository.list_jobs(db, limit=5)
            if jobs:
                lines.append("- Available job_ids: " + ", ".join(str(j.id) for j in jobs))
            else:
                lines.append("- No job descriptions analysed yet.")
        return "\n".join(lines)


career_agent = CareerAgent()
