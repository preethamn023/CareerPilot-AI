"""Tool 2: scrape_job_description - safe fetching of a public job page."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services import scrape_service
from app.tools.base import register_tool

_PARAMS = {
    "type": "object",
    "properties": {
        "url": {"type": "string", "description": "Public http(s) URL of the job description page"},
    },
    "required": ["url"],
}


@register_tool(
    "scrape_job_description",
    "Safely fetch a public job-description web page and return its cleaned text. "
    "Only public http/https URLs are allowed; private/internal addresses are blocked. "
    "Deterministic - no AI involved.",
    _PARAMS,
)
def scrape_job_description(db: Session, url: str) -> dict[str, Any]:
    page, cleaned = scrape_service.scrape_job_description(url)
    return {
        "url": page.url,
        "final_url": page.final_url,
        "title": cleaned.title or page.title,
        "meta_description": page.meta_description,
        "text": cleaned.text[:12000],
        "char_count": cleaned.char_count,
    }
