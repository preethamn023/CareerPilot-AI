/** TypeScript mirrors of the backend Pydantic schemas. */

export type ExtractionMethod = "gemini" | "glm_bridge" | "rule_based"
export type Importance = "high" | "medium" | "low"
export type Difficulty = "easy" | "medium" | "hard"
export type MatchType = "demonstrated" | "partial" | "listed"
export type QuestionCategory = "technical" | "programming" | "project" | "hr" | "behavioral" | "scenario"

export const ALL_CATEGORIES: QuestionCategory[] = [
  "technical",
  "programming",
  "project",
  "hr",
  "behavioral",
  "scenario",
]

export interface Education {
  degree?: string | null
  institution?: string | null
  year?: string | null
  score?: string | null
}

export interface Project {
  name?: string | null
  description?: string | null
  technologies: string[]
  key_contributions: string[]
}

export interface ExperienceItem {
  role?: string | null
  organization?: string | null
  duration?: string | null
  description?: string | null
}

export interface ResumeProfile {
  full_name?: string | null
  email?: string | null
  phone?: string | null
  location?: string | null
  professional_summary?: string | null
  education: Education[]
  technical_skills: string[]
  programming_languages: string[]
  frameworks: string[]
  tools_and_technologies: string[]
  projects: Project[]
  internships: ExperienceItem[]
  work_experience: ExperienceItem[]
  certifications: string[]
  achievements: string[]
  extraction_method: ExtractionMethod
}

export interface ResumeResponse {
  id: number
  filename: string
  char_count: number
  page_count: number
  extraction_method: ExtractionMethod
  profile: ResumeProfile | null
  created_at: string
  updated_at: string
}

export interface ResumeListItem {
  id: number
  filename: string
  full_name?: string | null
  char_count: number
  created_at: string
}

export interface JobDescriptionInfo {
  company?: string | null
  role?: string | null
  location?: string | null
  employment_type?: string | null
  experience_requirements?: string | null
  education_requirements?: string | null
  required_skills: string[]
  preferred_skills: string[]
  responsibilities: string[]
  qualifications: string[]
  salary_range?: string | null
  extraction_method: ExtractionMethod
}

export interface JobResponse {
  id: number
  source: string
  url?: string | null
  created_at: string
  extraction_method: ExtractionMethod
  job: JobDescriptionInfo
}

export interface JobListItem {
  id: number
  source: string
  url?: string | null
  role?: string | null
  company?: string | null
  created_at: string
}

export interface MatchedSkill {
  skill: string
  evidence?: string | null
  match_type: MatchType
}

export interface PartiallyMatchedSkill {
  skill: string
  evidence?: string | null
  match_type: MatchType
  reason_partial?: string | null
}

export interface MissingSkill {
  skill: string
  importance: Importance
  reason?: string | null
}

export interface ScoreDimension {
  name: string
  score: number
  weight: number
  explanation: string
}

export interface MatchResult {
  overall_match_score: number
  technical_skill_score: number
  education_score: number
  experience_score: number
  project_relevance_score: number
  matched_skills: MatchedSkill[]
  partially_matched_skills: PartiallyMatchedSkill[]
  missing_skills: MissingSkill[]
  resume_evidence: string[]
  unmet_requirements: string[]
  recommendations: string[]
  score_breakdown: ScoreDimension[]
  score_explanation: string
  analysis_method: ExtractionMethod
  disclaimer: string
}

export interface SkillGapItem {
  skill: string
  importance: Importance
  job_requirement_reason?: string | null
  current_resume_evidence?: string | null
  learning_approach?: string | null
  suggested_project?: string | null
  estimated_learning_duration?: string | null
}

export interface AnalysisReport {
  analysis_id: number
  resume_id: number
  job_id: number
  created_at: string
  job_role?: string | null
  company?: string | null
  match: MatchResult
  skill_gaps: SkillGapItem[]
}

export interface HistoryItem {
  analysis_id: number
  resume_id: number
  job_id: number
  job_role?: string | null
  company?: string | null
  overall_match_score: number
  analysis_method: ExtractionMethod
  created_at: string
}

export interface BulletOptimization {
  section: string
  original_bullet: string
  optimized_bullet: string
  improvement_rationale: string
  keywords_highlighted: string[]
  method: ExtractionMethod
}

export interface StoredOptimization extends BulletOptimization {
  id: number
  analysis_id?: number | null
  resume_id: number
  selected: boolean
  created_at: string
}

export interface OptimizeResponse {
  optimizations: BulletOptimization[]
  method: ExtractionMethod
  note?: string | null
}

export interface InterviewQuestion {
  question: string
  category: QuestionCategory
  difficulty: Difficulty
  why_asked?: string | null
  key_concepts: string[]
  answer_structure?: string | null
  method: ExtractionMethod
}

export interface StoredInterviewQuestion extends InterviewQuestion {
  id: number
}

export interface GenerateInterviewResponse {
  questions: StoredInterviewQuestion[]
  method: ExtractionMethod
  note?: string | null
}

export interface AnswerEvaluation {
  overall_feedback: string
  relevance_score: number
  clarity_score: number
  technical_accuracy_score: number
  completeness_score: number
  strengths: string[]
  improvements: string[]
  suggested_answer_outline?: string | null
  disclaimer: string
}

export interface EvaluateAnswerResponse {
  evaluation: AnswerEvaluation
  method: ExtractionMethod
}

export interface HealthResponse {
  status: string
  app_name: string
  version: string
  ai_provider: string
  ai_configured: boolean
  ai_model?: string | null
  database: string
  timestamp: string
}

export interface ApiErrorShape {
  message: string
  code?: string
  status?: number
}

export const METHOD_LABELS: Record<ExtractionMethod, string> = {
  gemini: "Gemini AI",
  glm_bridge: "GLM AI (sandbox)",
  rule_based: "Rule-based (offline)",
}
