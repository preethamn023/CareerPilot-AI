"""Deterministic PDF processing using PyMuPDF (fitz).

The LLM never touches file handling: validation, size checks and text
extraction are pure Python so they are testable and safe.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import pymupdf  # PyMuPDF

from app.config import settings
from app.services.exceptions import PDFValidationError, ScannedPDFError

PDF_MAGIC = b"%PDF-"


@dataclass
class PdfExtraction:
    text: str
    page_count: int
    char_count: int


def validate_upload(filename: str, content: bytes) -> None:
    """Validate file name, extension, magic bytes and size."""
    if not filename or not filename.lower().endswith(".pdf"):
        raise PDFValidationError("Only PDF files are accepted. Please upload a .pdf resume.")
    if len(content) == 0:
        raise PDFValidationError("The uploaded file is empty.")
    if len(content) > settings.max_upload_size_bytes:
        raise PDFValidationError(
            f"File is too large ({len(content) / (1024 * 1024):.1f} MB). "
            f"Maximum allowed size is {settings.max_upload_size_mb} MB."
        )
    if not content.startswith(PDF_MAGIC):
        raise PDFValidationError("The file is not a valid PDF document (missing PDF header).")


def extract_text_from_pdf(content: bytes) -> PdfExtraction:
    """Extract text from a PDF byte string.

    Raises:
        PDFValidationError: when the document cannot be opened at all.
        ScannedPDFError: when the PDF opens but contains no readable text
            (e.g. a scanned/image resume).
    """
    try:
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            pages: list[str] = []
            for page in doc:
                pages.append(page.get_text("text"))
            text = "\n".join(pages)
    except pymupdf.FileDataError as exc:
        raise PDFValidationError("The PDF file appears to be corrupted or malformed.") from exc
    except Exception as exc:  # noqa: BLE001 - any fitz failure must become a safe 422
        raise PDFValidationError("Could not read the PDF file.") from exc

    stripped = text.strip()
    if len(stripped) < settings.min_resume_text_chars:
        raise ScannedPDFError(
            "No readable text found in this PDF. It looks like a scanned or "
            "image-based resume. Please upload a text-based PDF (exported from "
            "Word, Google Docs or LaTeX)."
        )
    return PdfExtraction(text=stripped, page_count=len(pages), char_count=len(stripped))
