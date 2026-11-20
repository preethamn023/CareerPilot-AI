"""Application-level exceptions with user-safe messages."""
from __future__ import annotations


class CareerPilotError(Exception):
    """Base class. `message` is always safe to show to the end user."""

    code: str = "internal_error"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class PDFValidationError(CareerPilotError):
    code = "pdf_validation_error"


class ScannedPDFError(CareerPilotError):
    code = "scanned_pdf"


class ScrapeError(CareerPilotError):
    code = "scrape_error"


class LLMError(CareerPilotError):
    code = "llm_error"


class LLMNotConfiguredError(CareerPilotError):
    code = "llm_not_configured"


class NotFoundError(CareerPilotError):
    code = "not_found"
