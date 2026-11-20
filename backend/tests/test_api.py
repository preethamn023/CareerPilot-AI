"""Tests: REST API endpoints end-to-end (rule-based mode, no AI)."""
from __future__ import annotations

from tests.conftest import make_resume_pdf_bytes, make_scanned_pdf_bytes


class TestSystem:
    def test_health(self, client) -> None:  # noqa: ANN001
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["ai_provider"] == "none"  # no key, bridge disabled in tests
        assert body["database"] == "connected"

    def test_root_info(self, client) -> None:  # noqa: ANN001
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["app"] == "CareerPilot AI"


class TestResumeUpload:
    def test_upload_valid_pdf(self, client) -> None:  # noqa: ANN001
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", make_resume_pdf_bytes(), "application/pdf")},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["extraction_method"] == "rule_based"
        profile = body["profile"]
        assert profile["full_name"] == "Rahul Sharma"
        assert profile["email"] == "rahul.sharma@example.com"
        assert "Python" in profile["technical_skills"]

    def test_upload_scanned_pdf_rejected(self, client) -> None:  # noqa: ANN001
        response = client.post(
            "/api/resume/upload",
            files={"file": ("scanned.pdf", make_scanned_pdf_bytes(), "application/pdf")},
        )
        assert response.status_code == 422
        assert "scanned" in response.json()["detail"]["message"].lower()

    def test_upload_non_pdf_rejected(self, client) -> None:  # noqa: ANN001
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.txt", b"plain text resume content", "text/plain")},
        )
        assert response.status_code == 422

    def test_upload_invalid_pdf_bytes_rejected(self, client) -> None:  # noqa: ANN001
        response = client.post(
            "/api/resume/upload",
            files={"file": ("fake.pdf", b"not really a pdf %PDF-", "application/pdf")},
        )
        assert response.status_code == 422

    def test_get_resume(self, client) -> None:  # noqa: ANN001
        client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", make_resume_pdf_bytes(), "application/pdf")},
        )
        response = client.get("/api/resume/1")
        assert response.status_code == 200
        assert response.json()["profile"]["full_name"] == "Rahul Sharma"

    def test_get_missing_resume_404(self, client) -> None:  # noqa: ANN001
        response = client.get("/api/resume/999")
        assert response.status_code == 404

    def test_list_and_delete_resume(self, client) -> None:  # noqa: ANN001
        client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", make_resume_pdf_bytes(), "application/pdf")},
        )
        assert len(client.get("/api/resume").json()) == 1
        response = client.delete("/api/resume/1")
        assert response.status_code == 204
        assert client.get("/api/resume").json() == []


class TestJobs:
    def test_analyze_manual_text(self, client, jd_text: str) -> None:  # noqa: ANN001
        response = client.post("/api/jobs/analyze", json={"text": jd_text})
        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["source"] == "manual"
        assert "Python" in body["job"]["required_skills"]

    def test_analyze_empty_rejected(self, client) -> None:  # noqa: ANN001
        response = client.post("/api/jobs/analyze", json={})
        assert response.status_code == 422

    def test_analyze_short_text_rejected(self, client) -> None:  # noqa: ANN001
        response = client.post("/api/jobs/analyze", json={"text": "hiring devs"})
        assert response.status_code == 422

    def test_scrape_localhost_blocked(self, client) -> None:  # noqa: ANN001
        response = client.post("/api/jobs/scrape", json={"url": "http://127.0.0.1/secret"})
        assert response.status_code == 422
        message = response.json()["detail"]["message"].lower()
        assert "blocked" in message or "not allowed" in message or "internal" in message

    def test_scrape_bad_scheme_blocked(self, client) -> None:  # noqa: ANN001
        response = client.post("/api/jobs/scrape", json={"url": "ftp://example.com/jobs"})
        assert response.status_code == 422


class TestAnalysisFlow:
    def _setup(self, client, jd_text: str) -> tuple[int, int]:  # noqa: ANN001
        upload = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", make_resume_pdf_bytes(), "application/pdf")},
        )
        resume_id = upload.json()["id"]
        job = client.post("/api/jobs/analyze", json={"text": jd_text})
        job_id = job.json()["id"]
        return resume_id, job_id

    def test_match_analysis(self, client, jd_text: str) -> None:  # noqa: ANN001
        resume_id, job_id = self._setup(client, jd_text)
        response = client.post("/api/analysis/match", json={"resume_id": resume_id, "job_id": job_id})
        assert response.status_code == 201
        body = response.json()
        match = body["match"]
        assert 0 <= match["overall_match_score"] <= 100
        assert match["analysis_method"] == "rule_based"
        assert match["matched_skills"], "Python should match for this resume"
        assert match["missing_skills"], "Docker should be missing"
        assert match["score_breakdown"], "score must be explainable"
        assert body["skill_gaps"], "skill gaps expected"
        gap = body["skill_gaps"][0]
        assert gap["learning_approach"]
        assert gap["estimated_learning_duration"]

    def test_match_with_unknown_ids_404(self, client) -> None:  # noqa: ANN001
        response = client.post("/api/analysis/match", json={"resume_id": 50, "job_id": 60})
        assert response.status_code == 404

    def test_history_lifecycle(self, client, jd_text: str) -> None:  # noqa: ANN001
        resume_id, job_id = self._setup(client, jd_text)
        client.post("/api/analysis/match", json={"resume_id": resume_id, "job_id": job_id})
        history = client.get("/api/history").json()
        assert len(history) == 1
        assert history[0]["overall_match_score"] >= 0
        assert history[0]["job_role"] is not None

        report = client.get("/api/analysis/1")
        assert report.status_code == 200
        assert report.json()["match"]["overall_match_score"] == history[0]["overall_match_score"]

        delete = client.delete("/api/history/1")
        assert delete.status_code == 200
        assert client.get("/api/history").json() == []
        assert client.get("/api/analysis/1").status_code == 404

    def test_delete_missing_analysis_404(self, client) -> None:  # noqa: ANN001
        assert client.delete("/api/history/123").status_code == 404


class TestOptimizer:
    def test_optimize_bullets(self, client, jd_text: str) -> None:  # noqa: ANN001
        upload = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", make_resume_pdf_bytes(), "application/pdf")},
        )
        resume_id = upload.json()["id"]
        response = client.post("/api/resume/optimize", json={"resume_id": resume_id})
        assert response.status_code == 200
        body = response.json()
        assert body["method"] == "rule_based"
        assert body["optimizations"]
        for opt in body["optimizations"]:
            assert opt["original_bullet"]
            assert opt["optimized_bullet"]
            assert opt["improvement_rationale"]

    def test_selection_toggle(self, client) -> None:  # noqa: ANN001
        upload = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", make_resume_pdf_bytes(), "application/pdf")},
        )
        resume_id = upload.json()["id"]
        client.post("/api/resume/optimize", json={"resume_id": resume_id})
        listing = client.get("/api/optimizations").json()
        assert listing
        opt_id = listing[0]["id"]
        response = client.patch(f"/api/optimizations/{opt_id}", json={"selected": True})
        assert response.status_code == 200
        assert response.json()["selected"] is True

    def test_optimize_missing_resume_404(self, client) -> None:  # noqa: ANN001
        assert client.post("/api/resume/optimize", json={"resume_id": 9}).status_code == 404


class TestInterview:
    def test_generate_questions(self, client, jd_text: str) -> None:  # noqa: ANN001
        upload = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", make_resume_pdf_bytes(), "application/pdf")},
        )
        resume_id = upload.json()["id"]
        job = client.post("/api/jobs/analyze", json={"text": jd_text})
        job_id = job.json()["id"]
        response = client.post(
            "/api/interview/generate",
            json={
                "resume_id": resume_id,
                "job_id": job_id,
                "categories": ["technical", "hr"],
                "questions_per_category": 2,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["questions"]
        categories = {q["category"] for q in body["questions"]}
        assert categories <= {"technical", "hr"}
        for question in body["questions"]:
            assert question["question"]
            assert question["difficulty"] in ("easy", "medium", "hard")

    def test_invalid_category_rejected(self, client) -> None:  # noqa: ANN001
        upload = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", make_resume_pdf_bytes(), "application/pdf")},
        )
        resume_id = upload.json()["id"]
        response = client.post(
            "/api/interview/generate",
            json={"resume_id": resume_id, "categories": ["trickery"]},
        )
        assert response.status_code == 422

    def test_evaluate_requires_ai(self, client) -> None:  # noqa: ANN001
        response = client.post(
            "/api/interview/evaluate",
            json={"question": "Tell me about yourself", "answer": "I am a student."},
        )
        assert response.status_code == 503
        assert "GEMINI_API_KEY" in response.json()["detail"]["message"]


class TestAgent:
    def test_agent_status(self, client) -> None:  # noqa: ANN001
        response = client.get("/api/agent/status")
        assert response.status_code == 200
        body = response.json()
        assert body["ai"]["provider"] == "none"
        assert "calculate_match_score" in body["tools"]

    def test_agent_chat_requires_ai(self, client) -> None:  # noqa: ANN001
        response = client.post("/api/agent/chat", json={"message": "hello"})
        assert response.status_code == 503

    def test_agent_chat_empty_message_rejected(self, client) -> None:  # noqa: ANN001
        response = client.post("/api/agent/chat", json={"message": "  "})
        assert response.status_code == 422


class TestValidation:
    def test_match_payload_validation(self, client) -> None:  # noqa: ANN001
        response = client.post("/api/analysis/match", json={"resume_id": "one"})
        assert response.status_code == 422

    def test_404_for_unknown_api_route(self, client) -> None:  # noqa: ANN001
        assert client.get("/api/does-not-exist").status_code == 404
