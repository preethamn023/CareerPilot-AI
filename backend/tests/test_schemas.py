"""Tests: Pydantic schema validation, including the spec's example JSON."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.config import settings
from app.schemas.analysis import MatchResult
from app.schemas.interview import InterviewQuestion
from app.schemas.optimization import BulletOptimization
from app.schemas.resume import ResumeProfile

SPEC_EXAMPLE = {
    "overall_match_score": 78,
    "technical_skill_score": 82,
    "education_score": 90,
    "experience_score": 65,
    "project_relevance_score": 75,
    "matched_skills": [
        {"skill": "Python", "evidence": "Used in academic projects", "match_type": "demonstrated"}
    ],
    "missing_skills": [
        {"skill": "Docker", "importance": "high", "reason": "Required by the job description"}
    ],
    "recommendations": ["Build a practical Docker-based deployment project."],
}


def test_spec_example_validates() -> None:
    result = MatchResult.model_validate(SPEC_EXAMPLE)
    assert result.overall_match_score == 78
    assert result.matched_skills[0].skill == "Python"
    assert result.missing_skills[0].importance == "high"
    assert "not an employer ats score" in result.disclaimer.lower()


def test_missing_required_field_rejected() -> None:
    payload = dict(SPEC_EXAMPLE)
    del payload["technical_skill_score"]
    with pytest.raises(ValidationError):
        MatchResult.model_validate(payload)


def test_non_numeric_score_rejected() -> None:
    payload = dict(SPEC_EXAMPLE)
    payload["overall_match_score"] = "very high"
    with pytest.raises(ValidationError):
        MatchResult.model_validate(payload)


def test_invalid_importance_rejected() -> None:
    payload = json.loads(json.dumps(SPEC_EXAMPLE))
    payload["missing_skills"][0]["importance"] = "critical"
    with pytest.raises(ValidationError):
        MatchResult.model_validate(payload)


def test_resume_profile_allows_nulls() -> None:
    profile = ResumeProfile()
    assert profile.full_name is None
    assert profile.projects == []
    assert profile.extraction_method == "rule_based"


def test_interview_question_validates() -> None:
    question = InterviewQuestion(
        question="Explain Docker.",
        category="technical",
        difficulty="medium",
        why_asked="Listed in the job",
        key_concepts=["containers", "images"],
        answer_structure="Define, example, pitfall",
    )
    assert question.category == "technical"
    with pytest.raises(ValidationError):
        InterviewQuestion(question="x", category="not_a_category")  # type: ignore[arg-type]


def test_bullet_optimization_validates() -> None:
    bullet = BulletOptimization(
        original_bullet="worked on a project",
        optimized_bullet="Developed a project",
        improvement_rationale="Stronger verb",
        keywords_highlighted=["Python"],
    )
    assert bullet.section == "projects"


def test_scoring_weights_sum_to_one() -> None:
    total = (
        settings.weight_technical_skills
        + settings.weight_education
        + settings.weight_experience
        + settings.weight_project_relevance
    )
    assert abs(total - 1.0) < 1e-9
