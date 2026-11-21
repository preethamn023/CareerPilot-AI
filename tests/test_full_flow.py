import io
import sys
import json
import pymupdf as fitz
from fastapi.testclient import TestClient

sys.path.insert(0, "backend")
from app.config import get_settings
get_settings.cache_clear()
from app.config import settings
from app.main import app

client = TestClient(app)

print("=" * 70)
print("TASK 5: END-TO-END APPLICATION FUNCTIONALITY VERIFICATION")
print("=" * 70)

# 1. GET /api/health
print("\n[1] Testing GET /api/health...")
res_health = client.get("/api/health")
print("Status:", res_health.status_code)
health_data = res_health.json()
print("Health Data:", json.dumps(health_data, indent=2))
assert res_health.status_code == 200
assert health_data["status"] == "ok"
assert health_data["ai_provider"] == "gemini"
assert health_data["ai_configured"] is True
assert health_data["ai_model"] == settings.gemini_model
print(">>> GET /api/health PASSED!")

# 2. GET /api/agent/status
print("\n[2] Testing GET /api/agent/status...")
res_agent = client.get("/api/agent/status")
print("Status:", res_agent.status_code)
agent_data = res_agent.json()
print("Agent Status Data:", json.dumps(agent_data, indent=2))
assert res_agent.status_code == 200
assert agent_data["ai"]["provider"] == "gemini"
assert agent_data["ai"]["configured"] is True
assert len(agent_data["tools"]) > 0
print(">>> GET /api/agent/status PASSED!")

# 3. Create synthetic sample PDF resume and upload via POST /api/resume
print("\n[3] Creating synthetic sample PDF resume and testing POST /api/resume...")
doc = fitz.open()
page = doc.new_page(width=595, height=842)
y = 50
sample_resume_content = """Priya Nair
priya.nair@example.com | +91 91234 56789 | Hyderabad, India

OBJECTIVE
Motivated Computer Science graduate seeking an entry-level Backend Engineer role.

EDUCATION
B.Tech in Computer Science and Engineering, JNTU Hyderabad, 2022 - 2026, CGPA 8.8

TECHNICAL SKILLS
Languages: Python, JavaScript, SQL, C++
Frameworks: FastAPI, Flask, React
Databases: PostgreSQL, SQLite, Redis
Developer Tools: Docker, Git, GitHub, Linux, Postman

PROJECTS
Placement Portal Backend - Engineered a RESTful microservice using FastAPI, PostgreSQL,
and SQLAlchemy with JWT authentication and automated email alerts.
Real-Time Chat Application - Built a scalable messaging app utilizing WebSocket,
Redis pub/sub, and Docker containers.

INTERNSHIPS
Software Engineering Intern, CloudScale Innovations (May 2025 - Jul 2025)
Built automated REST API test pipelines and integrated Docker-based deployments.
"""
for line in sample_resume_content.splitlines():
    if line.strip():
        page.insert_text((50, y), line, fontsize=11)
        y += 18
    else:
        y += 8
pdf_bytes = doc.tobytes()
doc.close()

files = {"file": ("priya_nair_resume.pdf", pdf_bytes, "application/pdf")}
res_resume = client.post("/api/resume/upload", files=files)
print("Status:", res_resume.status_code)
resume_data = res_resume.json()
print("Resume Upload Response:", json.dumps(resume_data, indent=2))
assert res_resume.status_code == 201
resume_id = resume_data["id"]
print(f"Created Resume ID: {resume_id}")
assert resume_data["filename"] == "priya_nair_resume.pdf"
assert len(resume_data["profile"]["technical_skills"]) > 0
print(">>> PDF Resume Upload PASSED!")

# 4. Job description submission via POST /api/jobs/analyze
print("\n[4] Testing Job description submission via POST /api/jobs/analyze...")
jd_text = """Junior Backend Developer - Nexus Tech, Hyderabad

About the Role:
We are looking for a passionate Junior Backend Developer to design robust REST APIs.

Key Responsibilities:
- Build high-performance backend microservices using Python and FastAPI
- Design and manage relational databases using PostgreSQL and SQLAlchemy
- Write unit tests and maintain CI/CD pipelines with Docker and Git
- Collaborate with frontend engineers integrating React interfaces

Qualifications:
- Bachelor's degree in Computer Science, Information Technology, or relevant field
- Hands-on experience with Python and REST API frameworks (FastAPI/Flask/Django)
- Familiarity with SQL databases (PostgreSQL/MySQL) and Docker
- Strong analytical and problem-solving skills
"""

res_job = client.post("/api/jobs/analyze", json={"text": jd_text, "title": "Junior Backend Developer"})
print("Status:", res_job.status_code)
job_data = res_job.json()
print("Job Analysis Response:", json.dumps(job_data, indent=2))
assert res_job.status_code == 201
job_id = job_data["id"]
print(f"Created Job ID: {job_id}")
assert len(job_data["job"]["required_skills"]) > 0
print(">>> Job Description Submission PASSED!")

# 5. Resume analysis via POST /api/analysis/match
print(f"\n[5] Testing Resume Analysis via POST /api/analysis/match (resume_id={resume_id}, job_id={job_id})...")
res_match = client.post("/api/analysis/match", json={"resume_id": resume_id, "job_id": job_id})
print("Status:", res_match.status_code)
match_data = res_match.json()
print("Match Analysis Response:", json.dumps(match_data, indent=2))
assert res_match.status_code == 201
analysis_id = match_data["analysis_id"]
print(f"Created Analysis ID: {analysis_id}")
print(f"Overall Match Score: {match_data['match']['overall_match_score']}")
assert match_data["match"]["overall_match_score"] > 0
assert "score_breakdown" in match_data["match"]
assert len(match_data["skill_gaps"]) > 0
print(">>> Resume Analysis PASSED!")

# 6. Interview generation via POST /api/interview/generate
print(f"\n[6] Testing Interview generation via POST /api/interview/generate (resume_id={resume_id}, analysis_id={analysis_id})...")
res_interview = client.post("/api/interview/generate", json={
    "resume_id": resume_id,
    "job_id": job_id,
    "analysis_id": analysis_id,
    "categories": ["technical"],
    "questions_per_category": 2
})
print("Status:", res_interview.status_code)
interview_data = res_interview.json()
print("Interview Generation Response:", json.dumps(interview_data, indent=2))
assert res_interview.status_code == 201
assert len(interview_data["questions"]) > 0
print(f"Generated {len(interview_data['questions'])} mock interview questions successfully!")
print("Sample Question:", interview_data["questions"][0]["question"])
print(">>> Mock Interview Generation PASSED!")

print("\n" + "=" * 70)
print("ALL 6 END-TO-END WORKFLOW TESTS COMPLETED SUCCESSFULLY WITH REAL GEMINI AI!")
print("=" * 70)
