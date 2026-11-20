"""Tool 1: read_resume_pdf - read the extracted text of a stored PDF resume."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services import repository
from app.tools.base import register_tool

_PARAMS = {
    "type": "object",
    "properties": {
        "resume_id": {"type": "integer", "description": "ID of the stored resume to read"},
    },
    "required": ["resume_id"],
}


@register_tool(
    "read_resume_pdf",
    "Read the extracted text and metadata of a resume PDF that was previously uploaded. "
    "Returns the raw text (truncated), page count, char count and filename.",
    _PARAMS,
)
def read_resume_pdf(db: Session, resume_id: int) -> dict[str, Any]:
    resume = repository.get_resume(db, resume_id)
    profile = repository.resume_profile(resume)
    return {
        "resume_id": resume.id,
        "filename": resume.filename,
        "page_count": resume.page_count,
        "char_count": resume.char_count,
        "candidate_name": profile.full_name if profile else None,
        "text_preview": resume.raw_text[:4000],
        "extraction_method": resume.extraction_method,
    }
