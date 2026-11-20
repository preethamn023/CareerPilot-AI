"""Tests: PDF validation and text extraction (Module A, deterministic part)."""
from __future__ import annotations

import pytest

from app.config import settings
from app.services import pdf_service
from app.services.exceptions import PDFValidationError, ScannedPDFError


def test_extracts_text_from_valid_pdf(resume_pdf_bytes: bytes) -> None:
    result = pdf_service.extract_text_from_pdf(resume_pdf_bytes)
    assert "Rahul Sharma" in result.text
    assert "rahul.sharma@example.com" in result.text
    assert result.page_count >= 1
    assert result.char_count > 100


def test_extracts_all_sections(resume_pdf_bytes: bytes) -> None:
    result = pdf_service.extract_text_from_pdf(resume_pdf_bytes)
    for section in ("EDUCATION", "PROJECTS", "TECHNICAL SKILLS", "INTERNSHIPS"):
        assert section in result.text.upper()


def test_scanned_pdf_raises_friendly_error(scanned_pdf_bytes: bytes) -> None:
    with pytest.raises(ScannedPDFError) as exc_info:
        pdf_service.extract_text_from_pdf(scanned_pdf_bytes)
    assert "scanned" in str(exc_info.value).lower()


def test_invalid_magic_bytes_rejected() -> None:
    with pytest.raises(PDFValidationError):
        pdf_service.extract_text_from_pdf(b"this is not a pdf at all 1234567890")


def test_non_pdf_extension_rejected(resume_pdf_bytes: bytes) -> None:
    with pytest.raises(PDFValidationError):
        pdf_service.validate_upload("resume.docx", resume_pdf_bytes)


def test_empty_file_rejected() -> None:
    with pytest.raises(PDFValidationError):
        pdf_service.validate_upload("resume.pdf", b"")


def test_oversized_file_rejected(resume_pdf_bytes: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)  # 0 MB limit
    with pytest.raises(PDFValidationError) as exc_info:
        pdf_service.validate_upload("resume.pdf", resume_pdf_bytes)
    assert "too large" in str(exc_info.value).lower()


def test_corrupt_pdf_rejected() -> None:
    # Starts with the PDF magic but is broken afterwards.
    with pytest.raises(PDFValidationError):
        pdf_service.extract_text_from_pdf(b"%PDF-1.7 broken content \x00\x01\x02")
