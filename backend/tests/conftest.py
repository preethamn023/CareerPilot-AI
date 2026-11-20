"""Pytest configuration.

Isolation strategy (applied BEFORE the app is imported):
- No GEMINI_API_KEY -> Gemini provider disabled.
- AI_BRIDGE_ENABLED=false -> local bridge disabled -> rule-based mode.
- CP_DATABASE_URL points to a per-session temporary SQLite file.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.pop("GEMINI_API_KEY", None)
os.environ["GEMINI_API_KEY"] = ""
os.environ["AI_BRIDGE_ENABLED"] = "false"

_tmp_dir = tempfile.mkdtemp(prefix="careerpilot_test_")
os.environ["CP_DATABASE_URL"] = f"sqlite:///{_tmp_dir}/test.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.models.database import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture()
def client():
    """Fresh TestClient with a clean database per test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Direct SQLAlchemy session (clean database per test)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ----------------------------------------------------------------- fixtures
SAMPLE_RESUME_TEXT = """Rahul Sharma
rahul.sharma@example.com | +91 98765 43210 | Bengaluru, Karnataka

OBJECTIVE
Final-year MCA student seeking a software developer role.

EDUCATION
MCA - Master of Computer Applications, Bangalore University, 2023 - 2026, CGPA 8.6

TECHNICAL SKILLS
Programming Languages: Python, Java, JavaScript, SQL
Web: React, Node.js, HTML, CSS
Databases: MySQL, MongoDB
Tools: Git, GitHub, Linux

PROJECTS
Student Attendance Portal - Developed a full-stack web application using React,
Node.js, Express and MySQL to digitalise attendance for 4 departments.
Expense Tracker App - Built a Python and SQLite desktop application with
matplotlib reports.

INTERNSHIPS
Web Development Intern, TechSolutions Pvt Ltd (Jun 2025 - Aug 2025)
Worked on internal dashboards with React and REST APIs.

CERTIFICATIONS
Full Stack Web Development - NPTEL (2025)

ACHIEVEMENTS
Winner, Smart India Hackathon internal round (2024)
"""

SAMPLE_JD_TEXT = """Software Engineer (Fresher) - CloudPay Solutions, Bengaluru

We are hiring: Software Engineer - Fresher

Responsibilities:
- Develop and maintain web applications using Python and Django or Flask
- Build responsive user interfaces with React
- Work with relational databases such as PostgreSQL
- Deploy and operate services using Docker and basic AWS

Requirements:
- Bachelor or Master degree in Computer Science or related field (B.Tech / MCA / BCA)
- 0-2 years of experience; strong academic projects count
- Solid understanding of Python and JavaScript
- Knowledge of SQL databases and Git version control

Preferred skills (nice to have):
- Docker, Kubernetes
- AWS or other cloud platforms
- TypeScript
"""


def make_resume_pdf_bytes() -> bytes:
    import pymupdf as fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 50
    for line in SAMPLE_RESUME_TEXT.splitlines():
        if not line.strip():
            y += 6
            continue
        page.insert_text((50, y), line, fontname="helv", fontsize=10)
        y += 15
    data = doc.tobytes()
    doc.close()
    return data


def make_scanned_pdf_bytes() -> bytes:
    import pymupdf as fitz

    doc = fitz.open()
    doc.new_page(width=595, height=842)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture()
def resume_pdf_bytes() -> bytes:
    return make_resume_pdf_bytes()


@pytest.fixture()
def scanned_pdf_bytes() -> bytes:
    return make_scanned_pdf_bytes()


@pytest.fixture()
def resume_text() -> str:
    return SAMPLE_RESUME_TEXT


@pytest.fixture()
def jd_text() -> str:
    return SAMPLE_JD_TEXT
