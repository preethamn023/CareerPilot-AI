# CareerPilot AI

**AI-Powered Campus Placement & Resume Optimization Agent**

CareerPilot AI helps college students (B.Tech / MCA / BCA / B.Sc and other graduates, freshers and internship applicants) prepare for campus placements by analysing their resume against real job descriptions.

It is a genuinely functional AI agent application - not a chatbot wrapper or a UI mockup - with real PDF processing, safe job-page scraping, structured LLM analysis with Pydantic-validated outputs, an explainable scoring engine, and full persistence in SQLite.

> **Honesty note:** the match score is an explainable, AI-assisted estimate for preparation purposes only. It is **not** an employer ATS score and does not guarantee or predict selection. The UI states this wherever a score is shown.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Quick Start](#quick-start)
6. [Configuration (Environment Variables)](#configuration-environment-variables)
7. [AI Providers](#ai-providers)
8. [API Documentation](#api-documentation)
9. [Agent Tools](#agent-tools)
10. [Scoring Methodology](#scoring-methodology)
11. [Security](#security)
12. [Testing](#testing)
13. [Known Limitations](#known-limitations)
14. [Roadmap / Remaining Improvements](#roadmap--remaining-improvements)

---

## Features

| Module | What it does |
| --- | --- |
| **A. Resume Intelligence** | Drag-and-drop PDF upload, validation (type/size/magic bytes), scanned-PDF detection, structured extraction of name, contact, education, skills, projects, internships, experience, certifications and achievements. Never invents missing data - returns null/empty instead. |
| **B. Job Description Analyzer** | Paste text or analyse a public job URL. SSRF-hardened scraping (scheme/IP/DNS/port/redirect validation), HTML boilerplate removal, structured extraction of company, role, required/preferred skills, responsibilities and qualifications. |
| **C. Resume-Job Matching** | Explainable 0-100 compatibility score with sub-scores (technical skills, education, experience, project relevance), matched / partially matched / missing skills with quoted evidence, unmet requirements and actionable recommendations. |
| **D. Skill Gap Analysis** | Per-skill learning plan: importance, why the job needs it, current resume evidence, learning approach, suggested portfolio project and estimated duration. |
| **E. Resume Optimizer** | Improved bullet points with action verbs and relevant keywords - strictly truthful, rephrasing only what the resume already contains (no invented metrics, projects or achievements). Select-and-copy workflow. |
| **F. Mock Interview Agent** | Personalised technical / programming / project / HR / behavioral / scenario questions with difficulty, rationale, key concepts and answer structure. Optional AI evaluation of your practice answers (relevance, clarity, technical accuracy, completeness). |
| **Agent mode** | A conversational endpoint (`POST /api/agent/chat`) where the LLM picks tools via native function calling (Gemini) or JSON action selection (bridge) in a validated tool loop - max 6 tool calls per turn. |

The React dashboard provides: landing page, dashboard overview, resume upload, job analyzer, match report (gauge + radar chart + evidence), optimizer, interview prep and analysis history.

---

## Architecture

```
┌─────────────────────────── React + Vite (SPA, port 3000) ───────────────────────────┐
│  Landing / Dashboard / Resume / Jobs / Match / Optimizer / Interview / History       │
│  Tailwind CSS 4 + shadcn-style UI + Recharts + Axios (proxies /api -> 8000)          │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │ HTTP JSON (REST)
┌──────────────────────────────────────────▼───────────────────────────────────────────┐
│                            FastAPI (port 8000)                                        │
│  api/routes/*      REST endpoints (health, resume, jobs, analysis, optimizer,         │
│                    interview, history, agent) - Pydantic request/response models      │
│  agents/           orchestrator.py (deterministic pipelines + LLM tool loop),         │
│                    career_agent.py (tool validation & execution)                      │
│  tools/            8 registered tools (see Agent Tools below)                         │
│  services/         llm_service (Gemini / bridge / none), pdf_service (PyMuPDF),       │
│                    scrape_service (SSRF-safe requests + BeautifulSoup),               │
│                    ai_analysis (semantic prompts + schema validation),                │
│                    rule_based (deterministic offline engine), repository (SQLAlchemy) │
│  schemas/          Strict Pydantic models for every AI output                         │
│  models/           SQLAlchemy entities: Resume, JobDescription, Analysis,             │
│                    SkillGap, OptimizedBullet, InterviewQuestionRow (SQLite)           │
└───────────────┬──────────────────────────────────────────────┬───────────────────────┘
                │ google-genai SDK (primary)                   │ local AI bridge (fallback)
      ┌─────────▼──────────┐                        ┌──────────▼───────────┐
      │  Google Gemini     │                        │  mini-services/      │
      │  (GEMINI_API_KEY)  │                        │  ai-bridge (port     │
      │  structured JSON + │                        │  8010) wrapping the  │
      │  function calling  │                        │  sandbox LLM         │
      └────────────────────┘                        └──────────────────────┘
```

**Separation of concerns**

- **Deterministic Python** handles files, validation, URL safety, scoring math and database access.
- **The LLM** is used only for semantic understanding (extraction, classification, recommendations, content generation) and can only invoke registered tools with schema-validated arguments. It can never execute Python, shell commands or SQL.
- **Every AI output** is validated against a Pydantic schema before it is stored or returned; malformed responses are retried once, then surfaced as a safe error.

---

## Technology Stack

**Frontend:** React 19, TypeScript, Vite 6, Tailwind CSS 4, shadcn/ui-style components (Radix primitives), Lucide icons, Recharts, React Router 7, Axios, Sonner.

**Backend:** Python 3.12, FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2, SQLite, PyMuPDF, python-multipart, BeautifulSoup4 + lxml, Requests, httpx.

**AI:** Google Gemini via the official `google-genai` SDK (structured JSON output + native function calling). Optional local bridge for sandbox environments.

**Testing:** pytest + FastAPI TestClient (118 tests). Frontend: `tsc --noEmit` strict typecheck + Vite production build.

---

## Project Structure

```
CareerPilot-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, error handling, routers
│   │   ├── config.py               # pydantic-settings, all env vars
│   │   ├── api/routes/             # health, resume, jobs, analysis, optimizer,
│   │   │                           # interview, history, agent
│   │   ├── agents/
│   │   │   ├── orchestrator.py     # pipelines + LLM tool-calling loop
│   │   │   └── career_agent.py     # tool argument validation & execution
│   │   ├── tools/                  # 8 tools + registry (base.py)
│   │   ├── services/               # llm_service, pdf_service, scrape_service,
│   │   │                           # ai_analysis, rule_based, repository, exceptions
│   │   ├── schemas/                # Pydantic models (common/resume/job/analysis/
│   │   │                           # optimization/interview)
│   │   └── models/                 # database.py + entities.py (SQLAlchemy)
│   ├── tests/                      # 118 pytest tests
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/             # ui/ (shadcn-style), layout/, shared components
│   │   ├── pages/                  # Landing, Dashboard, ResumeUpload, JobAnalyzer,
│   │   │                           # MatchAnalysis, Optimizer, Interview, History
│   │   ├── services/api.ts         # typed Axios client
│   │   ├── store/AppContext.tsx    # app state (selections, health, lists)
│   │   ├── types/                  # TS mirrors of the Pydantic schemas
│   │   └── lib/utils.ts
│   ├── index.html / vite.config.ts / tsconfig.json
│   └── package.json
├── mini-services/ai-bridge/        # optional local AI bridge (bun + z-ai-web-dev-sdk)
├── scripts/dev.js                  # runs backend (8000) + frontend (3000) together
├── .env (root, sandbox infra)      # not used by the app
├── .gitignore
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+ and Node.js 18+ (or Bun)
- A Gemini API key (optional - the app falls back to rule-based mode without one)

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then edit .env (see below)
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
bun install                        # or: npm install
bun run dev                        # or: npm run dev   (serves on :3000, proxies /api)
```

Open http://localhost:3000

### 3. Both at once (root orchestrator)

```bash
bun install                        # root - no dependencies, instant
bun run dev                        # starts backend :8000 + frontend :3000
```

### Production build

```bash
cd frontend && bun run build       # tsc --noEmit + vite build -> frontend/dist
```

Serve `frontend/dist` from any static host and set `VITE_API_BASE_URL` to your deployed API base (or mount the build behind the same origin as the API).

---

## Configuration (Environment Variables)

Create `backend/.env` from `backend/.env.example`:

| Variable | Default | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key. **Primary AI provider.** |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Any currently supported Gemini model (e.g. `gemini-2.5-flash`, `gemini-2.5-pro`). |
| `AI_BRIDGE_ENABLED` | `true` | Use the optional local AI bridge when no Gemini key is set. |
| `AI_BRIDGE_URL` | `http://127.0.0.1:8010` | Bridge base URL. |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | CORS allow-list (comma separated). |
| `MAX_UPLOAD_SIZE_MB` | `5` | Resume upload size limit. |
| `SCRAPE_TIMEOUT_SECONDS` | `15` | Job-page fetch timeout. |
| `WEIGHT_TECHNICAL_SKILLS` | `0.40` | Scoring weight (must sum to 1.0 with the others). |
| `WEIGHT_EDUCATION` | `0.15` | Scoring weight. |
| `WEIGHT_EXPERIENCE` | `0.20` | Scoring weight. |
| `WEIGHT_PROJECT_RELEVANCE` | `0.25` | Scoring weight. |
| `CP_DATABASE_URL` | `sqlite:///./career_pilot.db` | SQLAlchemy database URL. |

Frontend (build-time, `frontend/.env`): `VITE_API_BASE_URL` (defaults to `/api`).

**Never commit `.env` files or real keys.** `.gitignore` excludes them.

---

## AI Providers

The backend selects a provider at request time:

1. **Gemini** (spec-compliant primary) - active when `GEMINI_API_KEY` is set. Uses `google-genai` structured JSON output (`response_schema` = Pydantic model) and native function calling for agent mode.
2. **Local AI bridge** - active when no Gemini key and `AI_BRIDGE_ENABLED=true`. A tiny Bun service (`mini-services/ai-bridge`, port 8010) exposes an OpenAI-style `/v1/chat/completions` endpoint. Structured output is achieved via strict prompting + lenient JSON parsing + one retry; agent tool choice uses JSON action selection.
3. **None (rule-based mode)** - deterministic keyword/section/alias analysis, clearly labelled `rule_based` in every response and shown as "Rule-based (offline)" in the UI. All workflows still function.

The active provider is visible on `GET /api/health` and in the dashboard header. Results are always labelled with the engine that produced them (`gemini` / `glm_bridge` / `rule_based`).

---

## API Documentation

Interactive docs are auto-generated at `/docs` (Swagger) and `/redoc` once the backend runs.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Service health: AI provider, DB status, version. |
| `POST` | `/api/resume/upload` | Upload a PDF resume (multipart `file`). Validates, extracts text, runs structured extraction. |
| `GET` | `/api/resume` | List stored resumes. |
| `GET` | `/api/resume/{resume_id}` | Resume with parsed profile. |
| `DELETE` | `/api/resume/{resume_id}` | Delete resume + its analyses. |
| `POST` | `/api/jobs/scrape` | Safe-scrape a public job URL and return cleaned text (no AI). |
| `POST` | `/api/jobs/analyze` | Analyse a job from `{url}` or `{text}` (+ optional `title`) and store it. |
| `GET` | `/api/jobs` / `GET /api/jobs/{id}` / `DELETE /api/jobs/{id}` | Job management. |
| `POST` | `/api/analysis/match` | `{resume_id, job_id}` -> full match report + skill gaps (stores an Analysis). |
| `GET` | `/api/analysis/{analysis_id}` | Stored report. |
| `GET` | `/api/history` | List previous analyses. |
| `DELETE` | `/api/history/{analysis_id}` | Delete an analysis (+ gaps, suggestions, questions). |
| `POST` | `/api/resume/optimize` | `{resume_id, job_id?}` -> truthful bullet-point suggestions. |
| `GET` | `/api/optimizations` | Stored suggestions. |
| `PATCH` | `/api/optimizations/{id}` | `{selected: bool}` selection toggle. |
| `POST` | `/api/interview/generate` | `{resume_id, job_id?, categories[], questions_per_category}` -> personalised questions. |
| `GET` | `/api/interview` | Stored questions. |
| `POST` | `/api/interview/evaluate` | `{question, answer, resume_id?, job_id?}` -> AI feedback (requires an AI provider). |
| `POST` | `/api/agent/chat` | Conversational agent with tool calling. |
| `GET` | `/api/agent/status` | Active AI engine + registered tools. |

Errors use a consistent shape: `{"detail": {"message": "<user-safe text>", "code": "<machine code>"}}` with proper status codes (404 not found, 422 validation, 503 AI unavailable).

Example - match response (abridged):

```json
{
  "analysis_id": 1,
  "job_role": "Software Engineer (Fresher)",
  "company": "CloudPay Solutions",
  "match": {
    "overall_match_score": 66,
    "technical_skill_score": 54,
    "education_score": 96,
    "experience_score": 78,
    "project_relevance_score": 64,
    "matched_skills": [
      { "skill": "Python", "evidence": "Built a Python and SQLite desktop application ... (Expense Tracker App project)", "match_type": "demonstrated" }
    ],
    "partially_matched_skills": [],
    "missing_skills": [
      { "skill": "Docker", "importance": "medium", "reason": "Required by the job description" }
    ],
    "score_breakdown": [ { "name": "Technical skills", "score": 54, "weight": 0.4, "explanation": "..." } ],
    "score_explanation": "Weighted score = 40% technical (54) + 15% education (96) + ...",
    "analysis_method": "gemini",
    "disclaimer": "This score is an explainable AI-assisted estimate ... not an employer ATS score ..."
  },
  "skill_gaps": [ { "skill": "Docker", "importance": "medium", "learning_approach": "...", "suggested_project": "...", "estimated_learning_duration": "2-3 weeks" } ]
}
```

---

## Agent Tools

Registered in `backend/app/tools/` and exposed to the LLM with strict JSON-schema parameters:

| Tool | Purpose |
| --- | --- |
| `read_resume_pdf` | Read stored resume text + metadata. |
| `scrape_job_description` | SSRF-safe fetch + clean of a public job page (deterministic). |
| `analyze_job_description` | Structured job info (AI or rule-based). |
| `extract_resume_information` | Structured resume profile (AI or rule-based). |
| `calculate_match_score` | Explainable match report. |
| `identify_skill_gaps` | Learning plan for missing/partial skills. |
| `optimize_resume_bullets` | Truthful bullet rewrites. |
| `generate_interview_questions` | Personalised question set. |

Product endpoints use deterministic pipelines (`orchestrator.run_pipeline`) for reliability; `POST /api/agent/chat` runs the LLM-driven loop (Gemini native function calling, or JSON action selection via the bridge) with argument validation, safe execution and a 6-step limit.

---

## Scoring Methodology

```
overall = 40% x technical + 15% x education + 20% x experience + 25% x project relevance
```

- **Technical**: deterministic credit per job skill - demonstrated = 1.0, partial = 0.5, listed = 0.3, missing = 0 - weighted 1.0 for required and 0.5 for preferred skills. With AI active, the skill statuses come from semantic classification (each with quoted evidence); the arithmetic is still pure Python.
- **Education / Experience / Project relevance**: AI judgement blended 65/35 with the rule-based baseline, clamped to 0-100, each with written reasoning.
- Every dimension, its weight and its explanation are returned in `score_breakdown` and rendered in the UI.

---

## Security

- Gemini API key only in `backend/.env`; never sent to the frontend; excluded from logs and error messages.
- PDF validation: extension, magic bytes, size cap, scanned-PDF detection.
- SSRF protection: http/https only; localhost/`.local`/`.internal`/`.lan` blocked; IP-literal and DNS-resolved addresses checked against loopback/private/link-local (incl. cloud metadata `169.254.169.254`)/reserved/multicast ranges; ports 80/443 only; redirects re-validated per hop (max 5); content-type, size and timeout caps.
- No CAPTCHA/paywall/authentication bypass - such pages return a clear error asking the user to paste the text.
- CORS restricted to configured origins; global error handler never leaks internals; no arbitrary code execution from the LLM (tools only, with schema-validated arguments).
- Local single-user MVP by design - no authentication is pretended to exist.

---

## Testing

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -q
```

**118 tests** covering: PDF extraction and all invalid-upload paths, URL validation and every SSRF vector (including DNS rebinding and redirect-to-localhost), HTML boilerplate removal, skill normalisation/fuzzy matching, deterministic scoring math, Pydantic schema validation (including the spec's example JSON), missing-API-key behaviour, bridge failure/malformed-JSON/retry handling, rule-based analysers, and every REST endpoint (upload, analyse, match, optimize, interview, evaluate, history CRUD, agent status).

Frontend: `bun run build` runs `tsc --noEmit` (strict) followed by the production Vite build.

Both were executed during development; all green at delivery time.

---

## Known Limitations

- **Single-user, local MVP** - no accounts/multi-tenancy; anyone with access to the server shares the database.
- **Scraping** is static-HTML only (requests + BeautifulSoup). JavaScript-heavy boards, CAPTCHAs or authenticated pages fail by design with a "paste manually" message. Playwright rendering is intentionally not bundled to keep the footprint small.
- **Rule-based mode** (no AI provider) is intentionally conservative: keyword/alias matching and template questions, clearly labelled in the UI.
- **Answer evaluation** requires an AI provider (returns 503 with setup instructions otherwise).
- Re-running a match for the same resume+job pair reuses the stored report (avoids duplicate AI cost); upload a new resume or job to force a fresh analysis.
- Gemini availability/quality depends on Google; the bridge depends on the sandbox environment.
- File upload progress is simulated client-side (single POST request).

---

## Roadmap / Remaining Improvements

- Multi-user auth (JWT) and per-user data isolation.
- Playwright-based rendering fallback for JS-heavy job pages.
- Streaming responses (SSE) for long AI operations.
- Resume re-export (generate an optimized PDF/DOCX).
- ATS keyword coverage checks and job-application tracking.
- Vector-based semantic skill matching to remove alias dictionary maintenance.
- Rate limiting and API keys for the public API.
