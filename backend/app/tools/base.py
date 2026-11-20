"""Tool registry for the CareerPilot agent.

Tools are the ONLY capabilities the LLM can invoke. Each tool:
- declares a strict JSON-schema parameter contract (validated before execution),
- runs deterministic Python for files, network, scoring and database access,
- uses the LLM only for semantic understanding inside its own implementation.

The LLM can never execute arbitrary Python, shell commands or SQL.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from sqlalchemy.orm import Session


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    handler: Callable[..., Any] | None = None

    def run(self, db: Session, **kwargs: Any) -> Any:
        if self.handler is None:  # pragma: no cover
            raise RuntimeError(f"Tool {self.name} has no handler")
        return self.handler(db=db, **kwargs)


REGISTRY: dict[str, Tool] = {}


def register_tool(name: str, description: str, parameters: dict[str, Any] | None = None) -> Callable:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        REGISTRY[name] = Tool(
            name=name,
            description=description,
            parameters=parameters or {"type": "object", "properties": {}},
            handler=func,
        )
        return func

    return decorator


def tool_specs() -> list[dict[str, Any]]:
    """Tool manifest for the agent prompt / function declarations."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        }
        for tool in REGISTRY.values()
    ]
