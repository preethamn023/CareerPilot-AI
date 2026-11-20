"""Tests: rule-based fallback analysers (offline mode)."""
from __future__ import annotations

from app.schemas.job import JobDescriptionInfo
from app.services import rule_based


class TestResumeProfileExtraction:
    def test_contact_details(self, resume_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        assert profile.full_name == "Rahul Sharma"
        assert profile.email == "rahul.sharma@example.com"
        assert "98765" in (profile.phone or "")

    def test_skills_found(self, resume_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        for skill in ("Python", "JavaScript", "React", "Git"):
            assert skill in profile.technical_skills
        assert "Python" in profile.programming_languages
        assert "React" in profile.frameworks

    def test_education_parsed(self, resume_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        assert any("MCA" in (e.degree or "") for e in profile.education)

    def test_projects_parsed(self, resume_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        assert any("Attendance" in (p.name or "") or "Attendance" in (p.description or "") for p in profile.projects)

    def test_method_labelled_rule_based(self, resume_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        assert profile.extraction_method == "rule_based"

    def test_no_fabrication_on_empty_sections(self) -> None:
        profile = rule_based.rule_based_resume_profile("John Doe\njohn@x.com\nSome random text")
        assert profile.education == []
        assert profile.projects == []
        assert profile.full_name == "John Doe"


class TestJobInfoExtraction:
    def test_skills_split_required_vs_preferred(self, jd_text: str) -> None:
        info = rule_based.rule_based_job_info(jd_text)
        assert "Python" in info.required_skills
        assert "JavaScript" in info.required_skills
        # Docker is in the preferred block.
        assert "Docker" in info.preferred_skills
        assert "Docker" not in info.required_skills

    def test_experience_requirement_found(self, jd_text: str) -> None:
        info = rule_based.rule_based_job_info(jd_text)
        assert info.experience_requirements is not None
        assert "0-2" in info.experience_requirements or "years" in info.experience_requirements

    def test_education_requirement_found(self, jd_text: str) -> None:
        info = rule_based.rule_based_job_info(jd_text)
        assert info.education_requirements is not None

    def test_responsibilities_extracted(self, jd_text: str) -> None:
        info = rule_based.rule_based_job_info(jd_text)
        assert info.responsibilities, "expected responsibilities bullets"
        assert any("Python" in r for r in info.responsibilities)


class TestSkillGaps:
    def test_gap_plan_generated(self, resume_text: str, jd_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        job = rule_based.rule_based_job_info(jd_text)
        match = rule_based.rule_based_match(profile, job, resume_text)
        gaps = rule_based.rule_based_skill_gaps(match, job)
        assert gaps, "expected skill gaps for a fresher resume"
        for gap in gaps:
            assert gap.learning_approach
            assert gap.suggested_project
            assert gap.estimated_learning_duration

    def test_docker_gap_has_curated_guidance(self, resume_text: str, jd_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        job = rule_based.rule_based_job_info(jd_text)
        match = rule_based.rule_based_match(profile, job, resume_text)
        gaps = rule_based.rule_based_skill_gaps(match, job)
        docker = next((g for g in gaps if g.skill == "Docker"), None)
        if docker is not None:  # Docker should be missing for this resume
            assert "Dockerfile" in (docker.learning_approach or "") or "container" in (docker.learning_approach or "").lower()


class TestBulletOptimization:
    def test_weak_verb_replaced(self) -> None:
        result = rule_based.rule_based_optimize_bullets(
            [("projects", "worked on a web app with Python and Flask")],
            job_keywords=["Python", "Flask"],
        )
        assert result
        assert "worked on" not in result[0].optimized_bullet.lower()
        assert "Developed" in result[0].optimized_bullet
        assert "Python" in result[0].keywords_highlighted

    def test_never_adds_unrelated_keywords(self) -> None:
        result = rule_based.rule_based_optimize_bullets(
            [("projects", "Built a Python CLI tool for file organisation")],
            job_keywords=["Kubernetes"],
        )
        assert "Kubernetes" not in result[0].optimized_bullet


class TestInterviewQuestions:
    def test_categories_respected(self, resume_text: str, jd_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        job = rule_based.rule_based_job_info(jd_text)
        questions = rule_based.rule_based_interview_questions(profile, job, ["hr", "behavioral"], 2)
        assert questions
        assert all(q.category in ("hr", "behavioral") for q in questions)

    def test_questions_grounded_in_resume(self, resume_text: str, jd_text: str) -> None:
        profile = rule_based.rule_based_resume_profile(resume_text)
        job = rule_based.rule_based_job_info(jd_text)
        questions = rule_based.rule_based_interview_questions(profile, job, ["project"], 2)
        assert questions
        # Project questions must reference an actual project name.
        assert any("Attendance Portal" in q.question for q in questions)
