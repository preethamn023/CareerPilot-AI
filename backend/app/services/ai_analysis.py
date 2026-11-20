"""AI-powered semantic analysis (Gemini primary / local bridge fallback).

Every function here sends a strictly-constrained prompt and validates the
response against a Pydantic schema. When no provider is available the
callers fall back to `rule_based` - these functions then raise
LLMNotConfiguredError, which the tool layer converts into a fallback.
"""
from __future__ import annotations

import json

from app.schemas.analysis import (
    AIJudgement,
    MatchResult,
    ScoreDimension,
    SkillClassificationList,
)
from app.schemas.interview import AnswerEvaluation, InterviewQuestion, InterviewQuestionList
from app.schemas.job import JobDescriptionInfo
from app.schemas.optimization import BulletOptimization
from app.schemas.resume import ResumeProfile
from app.services.llm_service import llm_service

ANTI_FABRICATION = (
    "RULES YOU MUST FOLLOW:\n"
    "- Extract ONLY information present in the provided text.\n"
    "- If a field is missing or uncertain, return null (or an empty list) for it.\n"
    "- NEVER invent names, companies, dates, numbers, metrics, skills, or achievements.\n"
    "- Keep original wording where possible; normalise only obvious casing.\n"
)

TRUTHFUL_REWRITE = (
    "REWRITE RULES:\n"
    "- You may ONLY rephrase information that exists in the original bullet.\n"
    "- NEVER add internships, projects, certifications, metrics or achievements that are not in the original.\n"
    "- Use measurable outcomes ONLY when they already appear in the original text.\n"
    "- Use strong action verbs, clear structure, and highlight the technologies actually used.\n"
)


def ai_extract_resume_profile(resume_text: str) -> ResumeProfile:
    system = (
        "You are a precise resume information extraction engine for a campus placement tool. "
        "You extract structured data from raw resume text.\n" + ANTI_FABRICATION
    )
    user = (
        "Extract the structured resume profile from the text below.\n"
        "Notes:\n"
        "- programming_languages / frameworks / tools_and_technologies: infer from the "
        "skills and project sections where possible; leave empty rather than guessing.\n"
        "- technical_skills: all technical skills found anywhere in the resume.\n"
        "- For projects, include name, description, technologies and key contributions when present.\n"
        "Set extraction_method to \"rule_based\" (the server overrides it).\n\n"
        f"RESUME TEXT:\n```\n{resume_text[:18000]}\n```"
    )
    profile = llm_service.complete_json(ResumeProfile, system, user)
    profile.extraction_method = _current_method()
    return profile


def ai_analyze_job_description(job_text: str) -> JobDescriptionInfo:
    system = (
        "You are a job-description analysis engine. You convert raw job posting text "
        "into structured data.\n" + ANTI_FABRICATION
    )
    user = (
        "Analyse the job description below and return the structured result.\n"
        "- required_skills: skills the employer explicitly requires.\n"
        "- preferred_skills: 'good to have' / 'nice to have' skills.\n"
        "- responsibilities and qualifications: concise bullet strings.\n"
        "- Return null for anything not stated.\n"
        "Set extraction_method to \"rule_based\" (the server overrides it).\n\n"
        f"JOB DESCRIPTION:\n```\n{job_text[:18000]}\n```"
    )
    info = llm_service.complete_json(JobDescriptionInfo, system, user)
    info.extraction_method = _current_method()
    return info


def ai_classify_skills(
    profile: ResumeProfile,
    job_info: JobDescriptionInfo,
    resume_text: str,
) -> SkillClassificationList:
    system = (
        "You are a resume-vs-job skill matching engine. For EVERY skill listed you must "
        "classify how the candidate's resume covers it.\n"
        "Statuses:\n"
        "- 'demonstrated': the resume shows the skill being USED in a project, internship, "
        "work experience or certification (evidence must quote or reference that usage).\n"
        "- 'partial': the skill is mentioned (e.g. in a skills list) but not clearly "
        "demonstrated through projects or experience.\n"
        "- 'listed': same as partial but present ONLY as a bare keyword with no context.\n"
        "- 'missing': the skill is genuinely absent from the resume.\n"
        "Distinguish carefully: a skill genuinely absent vs present-but-not-demonstrated vs "
        "demonstrated through projects or experience.\n"
        "- importance: 'high' for core required skills, 'medium' for other required, "
        "'low' for preferred.\n"
        "- evidence: short factual quote/reference from the resume, or null.\n"
        "NEVER fabricate evidence.\n"
    )
    user = (
        "JOB SKILLS TO CLASSIFY (required + preferred):\n"
        f"{json.dumps(job_info.required_skills + job_info.preferred_skills, ensure_ascii=False)}\n\n"
        "CANDIDATE RESUME (structured + raw):\n"
        f"{profile.model_dump_json(indent=None)[:6000]}\n\n"
        f"RAW RESUME TEXT:\n```\n{resume_text[:12000]}\n```"
    )
    return llm_service.complete_json(SkillClassificationList, system, user, temperature=0.0)


def ai_judge_dimensions(profile: ResumeProfile, job_info: JobDescriptionInfo, resume_text: str) -> AIJudgement:
    system = (
        "You are an explainable career-readiness assessor. Judge the candidate against this "
        "specific job on three dimensions, each 0-100 with reasoning:\n"
        "- education_score: does the resume meet the job's education requirement?\n"
        "- experience_score: does the resume meet the experience requirement (fresher roles "
        "should not be punished for 0 years if projects/internships exist)?\n"
        "- project_relevance_score: how relevant are the resume projects to this role?\n"
        "Also return resume_evidence (factual quotes proving suitability), unmet_requirements "
        "(important job requirements not demonstrated) and actionable recommendations.\n"
        "Be fair to freshers. NEVER invent facts.\n"
    )
    user = (
        f"JOB (structured):\n{job_info.model_dump_json(indent=None)[:4000]}\n\n"
        f"RESUME (structured):\n{profile.model_dump_json(indent=None)[:6000]}\n\n"
        f"RAW RESUME TEXT:\n```\n{resume_text[:10000]}\n```"
    )
    return llm_service.complete_json(AIJudgement, system, user, temperature=0.1)


def ai_optimize_bullets(
    bullets: list[tuple[str, str]],
    job_keywords: list[str],
    job_role: str | None,
) -> list[BulletOptimization]:
    system = (
        "You are a professional resume writer for campus placement candidates.\n" + TRUTHFUL_REWRITE
    )
    payload = [{"section": s, "bullet": b} for s, b in bullets]
    user = (
        f"TARGET ROLE: {job_role or 'not specified'}\n"
        f"TARGET KEYWORDS (use only when truthful): {json.dumps(job_keywords[:25], ensure_ascii=False)}\n\n"
        "Rewrite each bullet below to be more professional and relevant to the target role. "
        "For each, return section, original_bullet (unchanged), optimized_bullet, "
        "improvement_rationale (why it is better) and keywords_highlighted.\n\n"
        f"BULLETS:\n{json.dumps(payload, ensure_ascii=False)[:12000]}"
    )

    from pydantic import BaseModel, Field  # local import to keep module surface small

    class BulletList(BaseModel):
        bullets: list[BulletOptimization] = Field(default_factory=list)

    result = llm_service.complete_json(BulletList, system, user, temperature=0.3)
    for bullet in result.bullets:
        bullet.method = _current_method()
    return result.bullets


def ai_generate_interview_questions(
    profile: ResumeProfile,
    job_info: JobDescriptionInfo,
    categories: list[str],
    per_category: int,
) -> list[InterviewQuestion]:
    system = (
        "You are a technical interview panel member preparing personalised interview "
        "questions for a campus placement candidate.\n"
        "- Questions MUST be grounded in the candidate's actual resume and the actual job.\n"
        "- Do NOT generate generic questions unrelated to the candidate's background.\n"
        "- Categories: technical, programming, project, hr, behavioral, scenario.\n"
        "- difficulty: easy | medium | hard.\n"
        "- why_asked: why an interviewer would ask this.\n"
        "- key_concepts: concepts a good answer must cover.\n"
        "- answer_structure: how to structure the answer (e.g. STAR for behavioral).\n"
    )
    user = (
        f"Generate at least {per_category} question(s) for EACH of these categories: "
        f"{json.dumps(categories)}.\n\n"
        f"JOB:\n{job_info.model_dump_json(indent=None)[:4000]}\n\n"
        f"RESUME:\n{profile.model_dump_json(indent=None)[:6000]}"
    )
    result = llm_service.complete_json(InterviewQuestionList, system, user, temperature=0.4)
    for question in result.questions:
        question.method = _current_method()
    return result.questions


def ai_evaluate_answer(
    question: str,
    answer: str,
    profile: ResumeProfile | None,
    job_info: JobDescriptionInfo | None,
) -> AnswerEvaluation:
    system = (
        "You are an interview coach evaluating a candidate's practice answer.\n"
        "Score relevance, clarity, technical accuracy and completeness (0-100) and give "
        "actionable, specific feedback. Be encouraging but honest. Do not invent facts "
        "about the candidate.\n"
    )
    user = (
        f"QUESTION:\n{question}\n\n"
        f"CANDIDATE'S ANSWER:\n```\n{answer[:8000]}\n```\n\n"
        f"CANDIDATE RESUME CONTEXT (optional):\n{profile.model_dump_json(indent=None)[:3000] if profile else 'n/a'}\n\n"
        f"JOB CONTEXT (optional):\n{job_info.model_dump_json(indent=None)[:3000] if job_info else 'n/a'}"
    )
    return llm_service.complete_json(AnswerEvaluation, system, user, temperature=0.2)


def _technical_from_classifications(
    classifications: SkillClassificationList,
    job_info: JobDescriptionInfo,
    fallback: int,
) -> int:
    """Deterministic technical score derived from AI skill classifications.

    Weight per skill: required=1.0, preferred=0.5, unrecognised=0.75.
    Credit: demonstrated=1.0, partial=0.5, listed=0.3, missing=0."""
    if not classifications.classifications:
        return fallback
    required = [s.lower() for s in job_info.required_skills]
    preferred = [s.lower() for s in job_info.preferred_skills]

    def weight_for(skill: str) -> float:
        s = (skill or "").lower().strip()
        if not s:
            return 0.0
        if s in required:
            return 1.0
        if s in preferred:
            return 0.5
        for r in required:
            if len(s) >= 4 and (s in r or r in s):
                return 1.0
        for p in preferred:
            if len(s) >= 4 and (s in p or p in s):
                return 0.5
        return 0.75

    factors = {"demonstrated": 1.0, "partial": 0.5, "listed": 0.3, "missing": 0.0}
    total = gained = 0.0
    for c in classifications.classifications:
        w = weight_for(c.skill)
        total += w
        gained += w * factors.get(c.status, 0.0)
    if total <= 0:
        return fallback
    return max(0, min(100, round(100 * gained / total)))


def ai_skill_gaps(match_result: MatchResult, job_info: JobDescriptionInfo) -> list:
    """Learning recommendations for missing / partial skills (Module D)."""
    from pydantic import BaseModel, Field

    from app.schemas.analysis import SkillGapItem

    class GapList(BaseModel):
        gaps: list[SkillGapItem] = Field(default_factory=list)

    system = (
        "You are a career coach for engineering students preparing for campus placements.\n"
        "For each skill the candidate is missing or weak on, produce an actionable learning plan.\n"
        "RULES:\n"
        "- current_resume_evidence: quote what the resume shows today (null if nothing).\n"
        "- NEVER imply the student already has the skill.\n"
        "- learning_approach: concrete, specific steps (courses/docs/topics).\n"
        "- suggested_project: a small, buildable portfolio project.\n"
        "- estimated_learning_duration: realistic range for a student alongside studies.\n"
        "- importance: high/medium/low based on how central the skill is to THIS job.\n"
    )
    missing = [m.model_dump() for m in match_result.missing_skills]
    partial = [p.model_dump() for p in match_result.partially_matched_skills]
    user = (
        f"JOB ROLE: {job_info.role or 'not specified'} at {job_info.company or 'unknown company'}\n"
        f"REQUIRED SKILLS: {json.dumps(job_info.required_skills, ensure_ascii=False)}\n\n"
        f"MISSING SKILLS:\n{json.dumps(missing, ensure_ascii=False)}\n\n"
        f"PARTIAL SKILLS (listed but not demonstrated):\n{json.dumps(partial, ensure_ascii=False)}\n\n"
        "Return a learning plan for each skill above (missing first)."
    )
    result = llm_service.complete_json(GapList, system, user, temperature=0.2)
    return result.gaps


def _current_method() -> str:
    """Label stored on AI results so the UI can show which engine produced them."""
    provider = llm_service.provider_status()["provider"]
    return "gemini" if provider == "gemini" else "glm_bridge"


def merge_ai_match(
    base: MatchResult,
    classifications: SkillClassificationList,
    judgement: AIJudgement,
    job_info: JobDescriptionInfo,
) -> MatchResult:
    """Merge AI semantic output into the deterministic base result.

    Skills come from the AI classification (it saw the full context);
    the technical score is recomputed deterministically FROM those
    classifications using the same weights as the rule-based engine
    (demonstrated=1.0, partial=0.5, listed=0.3, missing=0);
    other dimensions blend the AI judgement with rule-based bounds;
    the overall score stays deterministic and explainable."""
    from app.config import settings

    matched, partial, missing = [], [], []
    for c in classifications.classifications:
        if c.status == "demonstrated":
            matched.append({"skill": c.skill, "evidence": c.evidence, "match_type": "demonstrated"})
        elif c.status in ("partial", "listed"):
            partial.append(
                {
                    "skill": c.skill,
                    "evidence": c.evidence or "Mentioned in the resume but not clearly demonstrated",
                    "match_type": "partial",
                    "reason_partial": c.reason or "Present but not demonstrated through projects or experience",
                }
            )
        else:
            missing.append(
                {
                    "skill": c.skill,
                    "importance": c.importance,
                    "reason": c.reason or "Required by the job description",
                }
            )

    # Deterministic technical score from the AI classifications.
    technical = _technical_from_classifications(classifications, job_info, base.technical_skill_score)

    # Blend AI dimension scores with rule-based scores (bounded) for stability.
    def blend(ai_val: int, rule_val: int) -> int:
        return max(0, min(100, round(0.65 * ai_val + 0.35 * rule_val)))

    education = blend(judgement.education_score, base.education_score)
    experience = blend(judgement.experience_score, base.experience_score)
    project_rel = blend(judgement.project_relevance_score, base.project_relevance_score)

    overall = round(
        settings.weight_technical_skills * technical
        + settings.weight_education * education
        + settings.weight_experience * experience
        + settings.weight_project_relevance * project_rel
    )

    method = _current_method()
    explanation = (
        f"Weighted score = {int(settings.weight_technical_skills * 100)}% technical ({technical}) + "
        f"{int(settings.weight_education * 100)}% education ({education}) + "
        f"{int(settings.weight_experience * 100)}% experience ({experience}) + "
        f"{int(settings.weight_project_relevance * 100)}% project relevance ({project_rel}). "
        f"Skills classified by AI ({method}); overall score computed deterministically in Python. "
        f"Education: {judgement.education_reasoning} Experience: {judgement.experience_reasoning} "
        f"Projects: {judgement.project_relevance_reasoning}"
    )

    return MatchResult(
        overall_match_score=max(0, min(100, overall)),
        technical_skill_score=technical,
        education_score=education,
        experience_score=experience,
        project_relevance_score=project_rel,
        matched_skills=matched,
        partially_matched_skills=partial,
        missing_skills=missing,
        resume_evidence=judgement.resume_evidence[:8],
        unmet_requirements=judgement.unmet_requirements[:8],
        recommendations=judgement.recommendations[:6],
        score_breakdown=[
            ScoreDimension(
                name="Technical skills",
                score=technical,
                weight=settings.weight_technical_skills,
                explanation=f"{len(matched)} demonstrated, {len(partial)} partial, {len(missing)} missing (AI classified)",
            ),
            ScoreDimension(
                name="Education", score=education, weight=settings.weight_education,
                explanation=judgement.education_reasoning[:300],
            ),
            ScoreDimension(
                name="Experience", score=experience, weight=settings.weight_experience,
                explanation=judgement.experience_reasoning[:300],
            ),
            ScoreDimension(
                name="Project relevance", score=project_rel, weight=settings.weight_project_relevance,
                explanation=judgement.project_relevance_reasoning[:300],
            ),
        ],
        score_explanation=explanation,
        analysis_method=method,
    )
