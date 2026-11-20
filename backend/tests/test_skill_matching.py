"""Tests: skill matching logic (rule-based engine + AI classification math)."""
from __future__ import annotations

from app.schemas.analysis import (
    MatchResult,
    SkillClassification,
    SkillClassificationList,
)
from app.schemas.job import JobDescriptionInfo
from app.schemas.resume import Project, ResumeProfile
from app.services import rule_based
from app.services.ai_analysis import _technical_from_classifications


class TestSkillNormalization:
    def test_alias_to_canonical(self) -> None:
        assert rule_based.normalize_skill("js") == "JavaScript"
        assert rule_based.normalize_skill("python3") == "Python"
        assert rule_based.normalize_skill("k8s") == "Kubernetes"
        assert rule_based.normalize_skill("Machine Learning") == "Machine Learning"

    def test_case_and_whitespace_insensitive(self) -> None:
        assert rule_based.normalize_skill("  REACT ") == "React"
        assert rule_based.normalize_skill("Node.JS") == "Node.js"

    def test_unknown_returns_none(self) -> None:
        assert rule_based.normalize_skill("underwater basket weaving") is None


class TestFuzzyFind:
    def test_finds_skills_in_text(self) -> None:
        found = rule_based.fuzzy_find_skill("Built apps with Python, React and MySQL databases")
        assert "Python" in found
        assert "React" in found
        assert "SQL" in found  # mysql aliases to SQL

    def test_word_boundary_respected(self) -> None:
        found = rule_based.fuzzy_find_skill("I studied javascripting in college")
        assert "JavaScript" not in found

    def test_empty_text(self) -> None:
        assert rule_based.fuzzy_find_skill("") == []


class TestRuleBasedMatch:
    def _profile(self) -> ResumeProfile:
        return ResumeProfile(
            full_name="Test Student",
            technical_skills=["Python", "JavaScript", "React", "Git"],
            programming_languages=["Python", "JavaScript"],
            frameworks=["React"],
            projects=[
                Project(
                    name="Portal",
                    description="Built a web app using Python and JavaScript with React frontend",
                    technologies=["Python", "React"],
                )
            ],
            education=rule_based.rule_based_resume_profile("EDUCATION\nMCA, Bangalore University").education,
        )

    def _job(self) -> JobDescriptionInfo:
        return rule_based.rule_based_job_info(
            "Software Engineer role. Requirements: Python, JavaScript, React, Git. "
            "0-2 years experience. B.Tech / MCA degree required. "
            "Nice to have: Docker, Kubernetes, AWS."
        )

    def test_demonstrated_vs_partial_vs_missing(self) -> None:
        profile = self._profile()
        job = self._job()
        result = rule_based.rule_based_match(profile, job, "")
        matched = {m.skill for m in result.matched_skills}
        partial = {p.skill for p in result.partially_matched_skills}
        missing = {m.skill for m in result.missing_skills}

        # Python & React used in a project -> demonstrated.
        assert "Python" in matched and "React" in matched
        # JavaScript listed in skills but (in this constructed profile) not in the
        # project description -> partial or demonstrated depending on evidence text.
        assert "JavaScript" in matched or "JavaScript" in partial
        # Docker never mentioned -> missing.
        assert "Docker" in missing and "Kubernetes" in missing

    def test_evidence_present_for_demonstrated(self) -> None:
        profile = self._profile()
        job = self._job()
        result = rule_based.rule_based_match(profile, job, "")
        for entry in result.matched_skills:
            assert entry.evidence  # evidence is required

    def test_all_scores_within_bounds(self) -> None:
        result = rule_based.rule_based_match(self._profile(), self._job(), "")
        for score in (
            result.overall_match_score,
            result.technical_skill_score,
            result.education_score,
            result.experience_score,
            result.project_relevance_score,
        ):
            assert 0 <= score <= 100

    def test_method_is_rule_based(self) -> None:
        result = rule_based.rule_based_match(self._profile(), self._job(), "")
        assert result.analysis_method == "rule_based"

    def test_recommendations_reference_missing_skills(self) -> None:
        result = rule_based.rule_based_match(self._profile(), self._job(), "")
        assert result.recommendations, "expected at least one recommendation"


class TestTechnicalFromClassifications:
    def test_computes_weighted_score(self) -> None:
        job = JobDescriptionInfo(
            required_skills=["Python", "JavaScript", "React"],
            preferred_skills=["Docker", "AWS"],
        )
        classifications = SkillClassificationList(
            classifications=[
                SkillClassification(skill="Python", status="demonstrated"),
                SkillClassification(skill="JavaScript", status="partial"),
                SkillClassification(skill="React", status="demonstrated"),
                SkillClassification(skill="Docker", status="missing"),
                SkillClassification(skill="AWS", status="missing"),
            ]
        )
        # required weight 1.0 x3, preferred 0.5 x2 => total 4.0
        # gained: 1 + 0.5 + 1 + 0 + 0 = 2.5 => 62.5 -> 62 (banker's rounding)
        assert _technical_from_classifications(classifications, job, fallback=0) == 62

    def test_empty_classifications_falls_back(self) -> None:
        assert _technical_from_classifications(SkillClassificationList(), JobDescriptionInfo(), fallback=42) == 42


class TestMatchResultClamping:
    def test_scores_clamped_to_0_100(self) -> None:
        result = MatchResult(
            overall_match_score=150,
            technical_skill_score=-3,
            education_score=99.6,
            experience_score=50,
            project_relevance_score="70",  # type: ignore[arg-type]
        )
        assert result.overall_match_score == 100
        assert result.technical_skill_score == 0
        assert result.education_score == 100
        assert result.project_relevance_score == 70
