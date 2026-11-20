"""SQLAlchemy ORM entities.

Only the data needed by the application is stored:
- Resume: filename, extracted text and the parsed profile JSON.
- JobDescription: source, url, raw text and parsed info JSON.
- Analysis: one resume-vs-job comparison with the full match report.
- SkillGap / OptimizedBullet / InterviewQuestion: per-analysis artefacts.

No passwords, no accounts - this MVP is an explicitly local single-user tool.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    profile_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(32), default="rule_based")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(16), default="manual")  # url | manual
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    info_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(32), default="rule_based")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    job_id: Mapped[int] = mapped_column(ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    overall_match_score: Mapped[int] = mapped_column(Integer, default=0)
    technical_skill_score: Mapped[int] = mapped_column(Integer, default=0)
    education_score: Mapped[int] = mapped_column(Integer, default=0)
    experience_score: Mapped[int] = mapped_column(Integer, default=0)
    project_relevance_score: Mapped[int] = mapped_column(Integer, default=0)
    analysis_method: Mapped[str] = mapped_column(String(32), default="rule_based")
    match_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    resume: Mapped[Resume] = relationship(back_populates="analyses")
    job: Mapped[JobDescription] = relationship(back_populates="analyses")
    skill_gaps: Mapped[list["SkillGap"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    optimized_bullets: Mapped[list["OptimizedBullet"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    interview_questions: Mapped[list["InterviewQuestionRow"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    skill: Mapped[str] = mapped_column(String(255))
    importance: Mapped[str] = mapped_column(String(16), default="medium")
    job_requirement_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_resume_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_approach: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_project: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_learning_duration: Mapped[str | None] = mapped_column(String(64), nullable=True)

    analysis: Mapped[Analysis] = relationship(back_populates="skill_gaps")


class OptimizedBullet(Base):
    __tablename__ = "optimized_bullets"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int | None] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    section: Mapped[str] = mapped_column(String(64), default="projects")
    original_bullet: Mapped[str] = mapped_column(Text)
    optimized_bullet: Mapped[str] = mapped_column(Text)
    improvement_rationale: Mapped[str] = mapped_column(Text, default="")
    keywords_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    method: Mapped[str] = mapped_column(String(32), default="rule_based")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    analysis: Mapped[Analysis | None] = relationship(back_populates="optimized_bullets")


class InterviewQuestionRow(Base):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int | None] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(32), default="technical")
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    why_asked: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_concepts_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    answer_structure: Mapped[str | None] = mapped_column(Text, nullable=True)
    method: Mapped[str] = mapped_column(String(32), default="rule_based")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    analysis: Mapped[Analysis | None] = relationship(back_populates="interview_questions")
