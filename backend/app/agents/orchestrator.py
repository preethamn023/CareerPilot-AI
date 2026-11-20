"""Orchestrator: the agent 'brain'.

Two complementary execution modes:

1. `run_pipeline` - deterministic task routing for the product API endpoints.
   Reliable, testable, provider-independent (AI is used inside tools).

2. `chat` - a true LLM tool-calling loop for the conversational agent
   endpoint. The model chooses tools; the CareerAgent validates and executes
   them; results are fed back until a final answer is produced. Works with
   native Gemini function calling or with the local bridge (prompt-based
   tool choice). Max 6 tool iterations per turn.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.career_agent import AgentStep, career_agent
from app.models.entities import Analysis
from app.schemas.job import JobDescriptionInfo
from app.services import repository, scrape_service
from app.services.exceptions import CareerPilotError
from app.services.llm_service import ToolAction, llm_service
from app.tools import get_tool

MAX_AGENT_STEPS = 6


@dataclass
class AgentChatResult:
    reply: str
    steps: list[AgentStep] = field(default_factory=list)
    provider: str = "none"


class Orchestrator:
    # ---------------------------------------------------------- pipelines
    def run_pipeline(self, task: str, db: Session, **params: Any) -> Any:
        if task == "analyze_resume":
            return self._pipeline_analyze_resume(db, **params)
        if task == "analyze_job":
            return self._pipeline_analyze_job(db, **params)
        if task == "match":
            return self._pipeline_match(db, **params)
        if task == "optimize":
            return self._pipeline_optimize(db, **params)
        if task == "interview":
            return self._pipeline_interview(db, **params)
        if task == "evaluate_answer":
            return self._pipeline_evaluate(db, **params)
        raise ValueError(f"Unknown pipeline task: {task}")

    def _pipeline_analyze_resume(self, db: Session, filename: str, content: bytes) -> dict[str, Any]:
        from app.services import pdf_service

        pdf_service.validate_upload(filename, content)
        extraction = pdf_service.extract_text_from_pdf(content)
        resume = repository.create_resume(db, filename, extraction.text, extraction.page_count)
        tool = get_tool("extract_resume_information")
        profile = tool.run(db, resume_id=resume.id)
        return {"resume": resume, "profile": profile}

    def _pipeline_analyze_job(
        self,
        db: Session,
        url: str | None,
        text: str | None,
        title: str | None = None,
    ) -> dict[str, Any]:
        scraped_note = None
        if url and not text:
            page, cleaned = scrape_service.scrape_job_description(url)
            text = cleaned.text
            title = title or cleaned.title or page.title
            url = page.final_url
            scraped_note = f"Scraped {len(text)} characters from the URL."
        if not text or len(text.strip()) < 80:
            raise CareerPilotError(
                "Job description text is missing or too short. Paste the job description manually.",
                code="invalid_job_text",
            )
        tool = get_tool("analyze_job_description")
        analyzed = tool.run(db, text=text)
        job = repository.create_job(
            db,
            source="url" if url else "manual",
            url=url,
            title=title,
            raw_text=text,
            info=analyzed.job,
        )
        return {"job": job, "info": analyzed.job, "note": analyzed.note or scraped_note}

    def _pipeline_match(self, db: Session, resume_id: int, job_id: int) -> dict[str, Any]:
        from app.tools.skill_gap import build_skill_gaps

        match, gaps = build_skill_gaps(db, resume_id, job_id)
        resume = repository.get_resume(db, resume_id)
        job = repository.get_job(db, job_id)
        analysis = repository.create_analysis(db, resume, job, match, gaps)
        return {"analysis": analysis, "match": match, "gaps": gaps}

    def _pipeline_optimize(
        self,
        db: Session,
        resume_id: int,
        job_id: int | None,
        analysis_id: int | None,
        bullets: list[str] | None,
    ) -> dict[str, Any]:
        from app.tools.resume_optimizer import build_optimizations

        optimizations, note = build_optimizations(db, resume_id, job_id, bullets)
        if analysis_id is None and job_id is not None:
            row = db.scalars(
                select(Analysis)
                .where(Analysis.resume_id == resume_id, Analysis.job_id == job_id)
                .order_by(Analysis.id.desc())
                .limit(1)
            ).first()
            analysis_id = row.id if row else None
        rows = repository.save_optimizations(db, resume_id, analysis_id, optimizations)
        return {"rows": rows, "optimizations": optimizations, "note": note}

    def _pipeline_interview(
        self,
        db: Session,
        resume_id: int,
        job_id: int | None,
        analysis_id: int | None,
        categories: list[str],
        per_category: int,
    ) -> dict[str, Any]:
        from app.tools.interview_generator import build_questions

        questions, note = build_questions(db, resume_id, job_id, categories, per_category)
        if analysis_id is None and job_id is not None:
            row = db.scalars(
                select(Analysis)
                .where(Analysis.resume_id == resume_id, Analysis.job_id == job_id)
                .order_by(Analysis.id.desc())
                .limit(1)
            ).first()
            analysis_id = row.id if row else None
        rows = repository.save_questions(db, analysis_id, questions)
        return {"rows": rows, "questions": questions, "note": note}

    def _pipeline_evaluate(
        self,
        db: Session,
        question: str,
        answer: str,
        resume_id: int | None,
        job_id: int | None,
    ) -> dict[str, Any]:
        from app.services import ai_analysis

        if not question.strip() or not answer.strip():
            raise CareerPilotError("Both the question and the answer are required.", code="invalid_input")
        profile = None
        job_info: JobDescriptionInfo | None = None
        if resume_id:
            profile = repository.resume_profile(repository.get_resume(db, resume_id))
        if job_id:
            job_info = repository.job_info(repository.get_job(db, job_id))
        evaluation = ai_analysis.ai_evaluate_answer(question, answer, profile, job_info)
        return {"evaluation": evaluation}

    # ---------------------------------------------------------------- chat
    def chat(
        self,
        db: Session,
        message: str,
        resume_id: int | None = None,
        job_id: int | None = None,
    ) -> AgentChatResult:
        provider = llm_service.require_provider()
        context = career_agent.build_context(db, resume_id, job_id)

        system = (
            "You are CareerPilot AI, an assistant for college students preparing for campus "
            "placements. You help analyse resumes, job descriptions, resume-job matching, "
            "skill gaps, resume improvement and interview preparation.\n\n"
            f"CURRENT CONTEXT:\n{context}\n\n"
            "RULES:\n"
            "- Use the provided tools for any analysis; never guess results.\n"
            "- Tool arguments must be integers for IDs and valid strings otherwise.\n"
            "- After tools return, briefly summarise the useful findings for the student.\n"
            "- Be honest and encouraging. Never invent resume content, scores or job facts.\n"
            "- If a needed resource is missing, tell the student exactly what to upload or do.\n"
        )

        conversation: list[dict[str, str]] = [{"role": "user", "content": message}]
        steps: list[AgentStep] = []

        for _ in range(MAX_AGENT_STEPS):
            decision = llm_service.choose_tool(system, conversation, career_agent.llm_tools())
            if isinstance(decision, ToolAction):
                step = career_agent.execute_tool(db, decision)
                steps.append(step)
                conversation.append(
                    {
                        "role": "assistant",
                        "content": f'I called the tool "{decision.tool}" with arguments '
                        f"{decision.arguments}.",
                    }
                )
                conversation.append(
                    {
                        "role": "user",
                        "content": f"TOOL RESULT ({'success' if step.ok else 'error'}): {step.summary}",
                    }
                )
                continue
            reply = decision if isinstance(decision, str) else "I could not complete that request."
            return AgentChatResult(reply=reply, steps=steps, provider=provider)

        return AgentChatResult(
            reply="I reached the tool-call limit for this request. Please narrow your question "
            "(for example: 'analyse resume 1 against job 2') and try again.",
            steps=steps,
            provider=provider,
        )


orchestrator = Orchestrator()
