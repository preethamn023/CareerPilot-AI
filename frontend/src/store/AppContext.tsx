import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react"
import * as api from "@/services/api"
import type { HealthResponse, HistoryItem, JobListItem, ResumeListItem } from "@/types"

interface AppState {
  health: HealthResponse | null
  resumes: ResumeListItem[]
  jobs: JobListItem[]
  history: HistoryItem[]
  activeResumeId: number | null
  activeJobId: number | null
  activeAnalysisId: number | null
  setActiveResume: (id: number | null) => void
  setActiveJob: (id: number | null) => void
  setActiveAnalysis: (id: number | null) => void
  refreshHealth: () => Promise<void>
  refreshData: () => Promise<void>
}

const AppContext = createContext<AppState | null>(null)

const STORAGE_KEY = "careerpilot.selection"

function loadStoredSelection(): { resumeId: number | null; jobId: number | null; analysisId: number | null } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { resumeId: null, jobId: null, analysisId: null }
    const parsed = JSON.parse(raw)
    return {
      resumeId: typeof parsed.resumeId === "number" ? parsed.resumeId : null,
      jobId: typeof parsed.jobId === "number" ? parsed.jobId : null,
      analysisId: typeof parsed.analysisId === "number" ? parsed.analysisId : null,
    }
  } catch {
    return { resumeId: null, jobId: null, analysisId: null }
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [resumes, setResumes] = useState<ResumeListItem[]>([])
  const [jobs, setJobs] = useState<JobListItem[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const stored = loadStoredSelection()
  const [activeResumeId, setActiveResumeId] = useState<number | null>(stored.resumeId)
  const [activeJobId, setActiveJobId] = useState<number | null>(stored.jobId)
  const [activeAnalysisId, setActiveAnalysisId] = useState<number | null>(stored.analysisId)

  const refreshHealth = useCallback(async () => {
    try {
      setHealth(await api.getHealth())
    } catch {
      setHealth(null)
    }
  }, [])

  const refreshData = useCallback(async () => {
    try {
      const [r, j, h] = await Promise.all([api.listResumes(), api.listJobs(), api.listHistory()])
      setResumes(r)
      setJobs(j)
      setHistory(h)
    } catch {
      // The dashboard shows its own offline state.
    }
  }, [])

  useEffect(() => {
    void refreshHealth()
    void refreshData()
  }, [refreshHealth, refreshData])

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ resumeId: activeResumeId, jobId: activeJobId, analysisId: activeAnalysisId }),
    )
  }, [activeResumeId, activeJobId, activeAnalysisId])

  const setActiveResume = useCallback((id: number | null) => setActiveResumeId(id), [])
  const setActiveJob = useCallback((id: number | null) => setActiveJobId(id), [])
  const setActiveAnalysis = useCallback((id: number | null) => setActiveAnalysisId(id), [])

  return (
    <AppContext.Provider
      value={{
        health,
        resumes,
        jobs,
        history,
        activeResumeId,
        activeJobId,
        activeAnalysisId,
        setActiveResume,
        setActiveJob,
        setActiveAnalysis,
        refreshHealth,
        refreshData,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useApp(): AppState {
  const context = useContext(AppContext)
  if (!context) throw new Error("useApp must be used inside AppProvider")
  return context
}
