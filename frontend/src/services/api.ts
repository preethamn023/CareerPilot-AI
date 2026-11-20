import axios from "axios"
import type {
  AnalysisReport,
  AnswerEvaluation,
  ApiErrorShape,
  EvaluateAnswerResponse,
  GenerateInterviewResponse,
  HealthResponse,
  HistoryItem,
  JobListItem,
  JobResponse,
  OptimizeResponse,
  QuestionCategory,
  ResumeListItem,
  ResumeResponse,
  StoredOptimization,
} from "@/types"

/**
 * Axios client for the CareerPilot FastAPI backend.
 * In dev/preview the Vite server proxies /api to http://127.0.0.1:8000.
 * For other deployments set VITE_API_BASE_URL (e.g. https://api.example.com/api).
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 300_000, // AI operations can legitimately take a while
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error?.response?.data?.detail
    const message =
      typeof detail === "string"
        ? detail
        : detail?.message || error?.message || "The request failed. Please try again."
    const shaped: ApiErrorShape = {
      message,
      code: detail?.code,
      status: error?.response?.status,
    }
    return Promise.reject(shaped)
  },
)

export const errMessage = (error: unknown): string => {
  if (typeof error === "object" && error !== null && "message" in error) {
    return String((error as ApiErrorShape).message)
  }
  return "Something went wrong. Please try again."
}

/* ------------------------------------------------------------------ system */
export const getHealth = () => api.get<HealthResponse>("/health").then((r) => r.data)

/* ------------------------------------------------------------------ resume */
export const uploadResume = (file: File) => {
  const form = new FormData()
  form.append("file", file)
  return api.post<ResumeResponse>("/resume/upload", form).then((r) => r.data)
}
export const listResumes = () => api.get<ResumeListItem[]>("/resume").then((r) => r.data)
export const getResume = (id: number) => api.get<ResumeResponse>(`/resume/${id}`).then((r) => r.data)
export const deleteResume = (id: number) => api.delete(`/resume/${id}`)

/* -------------------------------------------------------------------- jobs */
export const analyzeJobFromText = (text: string, title?: string) =>
  api.post<JobResponse>("/jobs/analyze", { text, title }).then((r) => r.data)
export const analyzeJobFromUrl = (url: string) =>
  api.post<JobResponse>("/jobs/analyze", { url }).then((r) => r.data)
export const listJobs = () => api.get<JobListItem[]>("/jobs").then((r) => r.data)
export const getJob = (id: number) => api.get<JobResponse>(`/jobs/${id}`).then((r) => r.data)
export const deleteJob = (id: number) => api.delete(`/jobs/${id}`)

/* ---------------------------------------------------------------- analysis */
export const runMatch = (resumeId: number, jobId: number) =>
  api
    .post<AnalysisReport>("/analysis/match", { resume_id: resumeId, job_id: jobId })
    .then((r) => r.data)
export const getAnalysis = (id: number) =>
  api.get<AnalysisReport>(`/analysis/${id}`).then((r) => r.data)

/* ----------------------------------------------------------------- history */
export const listHistory = () => api.get<HistoryItem[]>("/history").then((r) => r.data)
export const deleteAnalysis = (id: number) => api.delete(`/history/${id}`).then((r) => r.data)

/* --------------------------------------------------------------- optimizer */
export const optimizeBullets = (resumeId: number, jobId?: number | null) =>
  api
    .post<OptimizeResponse>("/resume/optimize", { resume_id: resumeId, job_id: jobId ?? undefined })
    .then((r) => r.data)
export const listOptimizations = (resumeId?: number) =>
  api
    .get<StoredOptimization[]>("/optimizations", { params: resumeId ? { resume_id: resumeId } : {} })
    .then((r) => r.data)
export const setOptimizationSelected = (id: number, selected: boolean) =>
  api.patch(`/optimizations/${id}`, { selected }).then((r) => r.data)

/* --------------------------------------------------------------- interview */
export const generateInterviewQuestions = (
  resumeId: number,
  jobId: number | null,
  categories: QuestionCategory[],
  perCategory = 5,
) =>
  api
    .post<GenerateInterviewResponse>("/interview/generate", {
      resume_id: resumeId,
      job_id: jobId ?? undefined,
      categories,
      questions_per_category: perCategory,
    })
    .then((r) => r.data)
export const evaluateAnswer = (
  question: string,
  answer: string,
  resumeId?: number | null,
  jobId?: number | null,
) =>
  api
    .post<EvaluateAnswerResponse>("/interview/evaluate", {
      question,
      answer,
      resume_id: resumeId ?? undefined,
      job_id: jobId ?? undefined,
    })
    .then((r) => r.data)
export type { AnswerEvaluation }
