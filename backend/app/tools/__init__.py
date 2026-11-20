"""Import all tool modules so they register themselves in the registry."""
from app.tools.base import REGISTRY, Tool, register_tool, tool_specs  # noqa: F401
from app.tools import (  # noqa: F401
    interview_generator,
    job_analyzer,
    job_scraper,
    resume_extractor,
    resume_optimizer,
    resume_reader,
    skill_gap,
    skill_matcher,
)


def get_tool(name: str) -> Tool:
    if name not in REGISTRY:
        raise KeyError(f"Unknown tool: {name}")
    return REGISTRY[name]
