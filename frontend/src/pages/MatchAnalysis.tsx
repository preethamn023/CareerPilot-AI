import { useCallback, useEffect, useMemo, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts"
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Gauge as GaugeIcon,
  Info,
  Lightbulb,
  XCircle,
} from "lucide-react"
import * as apiClient from "@/services/api"
import { errMessage } from "@/services/api"
import { useApp } from "@/store/AppContext"
import type { AnalysisReport } from "@/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/EmptyState"
import { MethodBadge } from "@/components/MethodBadge"
import { ScoreGauge } from "@/components/ScoreGauge"
import { SkillChip } from "@/components/SkillChip"

export default function MatchAnalysis() {
  const { resumes, jobs, activeResumeId, activeJobId, setActiveResume, setActiveJob, setActiveAnalysis, history } = useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<AnalysisReport | null>(null)

  const storedAnalysisId = searchParams.get("analysis")

  const loadStored = useCallback(async (id: number) => {
    setLoading(true)
    try {
      const stored = await apiClient.getAnalysis(id)
      setReport(stored)
      setActiveResume(stored.resume_id)
      setActiveJob(stored.job_id)
      setActiveAnalysis(stored.analysis_id)
    } catch (error) {
      toast.error("Could not load report", { description: errMessage(error) })
      setReport(null)
    } finally {
      setLoading(false)
    }
  }, [setActiveAnalysis, setActiveJob, setActiveResume])

  useEffect(() => {
    if (storedAnalysisId) {
      void loadStored(Number(storedAnalysisId))
    }
  }, [storedAnalysisId, loadStored])

  const runAnalysis = async () => {
    if (!activeResumeId || !activeJobId) {
      toast.error("Select both a resume and a job description")
      return
    }
    setLoading(true)
    setReport(null)
    try {
      const result = await apiClient.runMatch(activeResumeId, activeJobId)
      setReport(result)
      setActiveAnalysis(result.analysis_id)
      setSearchParams({ analysis: String(result.analysis_id) }, { replace: true })
      toast.success("Match analysis complete", {
        description: `Overall score: ${result.match.overall_match_score}/100`,
      })
    } catch (error) {
      toast.error("Analysis failed", { description: errMessage(error) })
    } finally {
      setLoading(false)
    }
  }

  const match = report?.match
  const radarData = useMemo(() => {
    if (!match) return []
    return [
      { dimension: "Technical", score: match.technical_skill_score },
      { dimension: "Education", score: match.education_score },
      { dimension: "Experience", score: match.experience_score },
      { dimension: "Projects", score: match.project_relevance_score },
    ]
  }, [match])

  return (
    <div className="space-y-8">
      {/* Selectors */}
      <Card>
        <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="select-resume" className="mb-1.5 block text-sm font-medium">
              Resume
            </label>
            <Select
              value={activeResumeId ? String(activeResumeId) : undefined}
              onValueChange={(v) => setActiveResume(Number(v))}
            >
              <SelectTrigger id="select-resume" className="w-full">
                <SelectValue placeholder="Select a resume" />
              </SelectTrigger>
              <SelectContent>
                {resumes.map((resume) => (
                  <SelectItem key={resume.id} value={String(resume.id)}>
                    {resume.full_name ?? resume.filename} (#{resume.id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex-1">
            <label htmlFor="select-job" className="mb-1.5 block text-sm font-medium">
              Job description
            </label>
            <Select
              value={activeJobId ? String(activeJobId) : undefined}
              onValueChange={(v) => setActiveJob(Number(v))}
            >
              <SelectTrigger id="select-job" className="w-full">
                <SelectValue placeholder="Select a job" />
              </SelectTrigger>
              <SelectContent>
                {jobs.map((job) => (
                  <SelectItem key={job.id} value={String(job.id)}>
                    {job.role ?? `Job #${job.id}`}
                    {job.company ? ` - ${job.company}` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            onClick={() => void runAnalysis()}
            disabled={loading || !activeResumeId || !activeJobId}
            size="lg"
          >
            {loading ? "Analysing..." : "Run analysis"}
            {!loading && <ArrowRight className="size-4" aria-hidden />}
          </Button>
        </CardContent>
      </Card>

      {loading && !report && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardContent className="flex flex-col items-center gap-4 p-6">
              <Skeleton className="h-44 w-44 rounded-full" />
              <Skeleton className="h-4 w-32" />
            </CardContent>
          </Card>
          <Card className="lg:col-span-2">
            <CardContent className="space-y-4 p-6">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6" />
              <Skeleton className="h-3 w-4/6" />
              <Skeleton className="h-3 w-full" />
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && !report && resumes.length === 0 && jobs.length === 0 && (
        <EmptyState
          icon={GaugeIcon}
          title="Nothing to compare yet"
          description="Upload a resume and analyse a job description first - then come back to run the match analysis."
          action={
            <div className="flex gap-2">
              <Button asChild size="sm" variant="outline">
                <a href="/resume">Upload resume</a>
              </Button>
              <Button asChild size="sm" variant="outline">
                <a href="/jobs">Analyse a job</a>
              </Button>
            </div>
          }
        />
      )}

      {!loading && !report && (resumes.length > 0 || jobs.length > 0) && history.length > 0 && (
        <EmptyState
          icon={GaugeIcon}
          title="Ready when you are"
          description="Pick a resume and a job above, then run the analysis. You can also reopen one of your previous reports from the history page."
          action={
            <Button asChild size="sm" variant="outline">
              <a href="/history">View history</a>
            </Button>
          }
        />
      )}

      {match && report && (
        <>
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold">
                {report.job_role ?? "Job"} {report.company ? `at ${report.company}` : ""}
              </h2>
              <p className="text-sm text-muted-foreground">
                Analysed on {new Date(report.created_at).toLocaleString()}
              </p>
            </div>
            <MethodBadge method={match.analysis_method} />
          </div>

          {/* Score + dimensions */}
          <div className="grid gap-6 lg:grid-cols-3">
            <Card>
              <CardContent className="flex flex-col items-center p-6">
                <ScoreGauge score={match.overall_match_score} />
                <p className="mt-3 text-center text-xs leading-relaxed text-muted-foreground">
                  {match.disclaimer}
                </p>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base">Score breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {match.score_breakdown.map((dim) => (
                  <div key={dim.name}>
                    <div className="mb-1 flex items-baseline justify-between gap-2 text-sm">
                      <span className="font-medium">
                        {dim.name}
                        <span className="ml-2 text-xs text-muted-foreground">
                          weight {Math.round(dim.weight * 100)}%
                        </span>
                      </span>
                      <span className="font-semibold">{dim.score}</span>
                    </div>
                    <Progress value={dim.score} aria-label={`${dim.name}: ${dim.score} out of 100`} />
                    <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{dim.explanation}</p>
                  </div>
                ))}
                <div className="rounded-lg bg-slate-50 p-3 text-xs leading-relaxed text-muted-foreground">
                  <Info className="mr-1 inline size-3.5" aria-hidden />
                  {match.score_explanation}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Radar */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Dimension profile</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData} outerRadius="72%">
                      <PolarGrid stroke="#e2e8f0" />
                      <PolarAngleAxis dataKey="dimension" tick={{ fill: "#475569", fontSize: 12 }} />
                      <Radar dataKey="score" stroke="#2563eb" fill="#2563eb" fillOpacity={0.25} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Lightbulb className="size-4 text-primary" aria-hidden /> Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                {match.recommendations.length > 0 ? (
                  <ul className="space-y-2.5">
                    {match.recommendations.map((rec, i) => (
                      <li key={i} className="flex gap-2.5 text-sm leading-relaxed">
                        <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-bold text-primary">
                          {i + 1}
                        </span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No recommendations generated.</p>
                )}
                {match.unmet_requirements.length > 0 && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
                    <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-700">
                      <AlertTriangle className="size-3.5" aria-hidden /> Important requirements not demonstrated
                    </p>
                    <ul className="mt-1.5 list-inside list-disc space-y-1 text-xs text-amber-700">
                      {match.unmet_requirements.map((req, i) => (
                        <li key={i}>{req}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Skill columns */}
          <div className="grid gap-6 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <CheckCircle2 className="size-4 text-emerald-600" aria-hidden /> Matched
                  <span className="ml-auto text-sm font-normal text-muted-foreground">
                    {match.matched_skills.length}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="cp-scroll max-h-96 space-y-3 overflow-y-auto">
                {match.matched_skills.length === 0 && (
                  <p className="text-sm text-muted-foreground">No matched skills.</p>
                )}
                {match.matched_skills.map((skill) => (
                  <div key={skill.skill} className="rounded-lg border bg-emerald-50/40 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold">{skill.skill}</p>
                      <SkillChip label="demonstrated" tone="success" />
                    </div>
                    {skill.evidence && (
                      <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                        "{skill.evidence}"
                      </p>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <AlertTriangle className="size-4 text-amber-500" aria-hidden /> Partial
                  <span className="ml-auto text-sm font-normal text-muted-foreground">
                    {match.partially_matched_skills.length}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="cp-scroll max-h-96 space-y-3 overflow-y-auto">
                {match.partially_matched_skills.length === 0 && (
                  <p className="text-sm text-muted-foreground">No partially matched skills.</p>
                )}
                {match.partially_matched_skills.map((skill) => (
                  <div key={skill.skill} className="rounded-lg border bg-amber-50/40 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold">{skill.skill}</p>
                      <SkillChip label="partial" tone="warning" />
                    </div>
                    {(skill.reason_partial || skill.evidence) && (
                      <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                        {skill.reason_partial ?? skill.evidence}
                      </p>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <XCircle className="size-4 text-red-500" aria-hidden /> Missing
                  <span className="ml-auto text-sm font-normal text-muted-foreground">
                    {match.missing_skills.length}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="cp-scroll max-h-96 space-y-3 overflow-y-auto">
                {match.missing_skills.length === 0 && (
                  <p className="text-sm text-muted-foreground">No missing skills - impressive!</p>
                )}
                {match.missing_skills.map((skill) => (
                  <div key={skill.skill} className="rounded-lg border bg-red-50/40 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold">{skill.skill}</p>
                      <SkillChip
                        label={skill.importance}
                        tone={skill.importance === "high" ? "danger" : skill.importance === "medium" ? "warning" : "neutral"}
                      />
                    </div>
                    {skill.reason && (
                      <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{skill.reason}</p>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Skill gaps */}
          {report.skill_gaps.length > 0 && (
            <section>
              <h3 className="mb-3 flex items-center gap-2 text-base font-semibold">
                <BookOpen className="size-4 text-primary" aria-hidden /> Skill gap learning plan
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                {report.skill_gaps.map((gap) => (
                  <Card key={gap.skill}>
                    <CardContent className="space-y-3 p-5">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-semibold">{gap.skill}</p>
                        <SkillChip
                          label={`${gap.importance} priority`}
                          tone={gap.importance === "high" ? "danger" : gap.importance === "medium" ? "warning" : "neutral"}
                        />
                      </div>
                      {gap.job_requirement_reason && (
                        <p className="text-xs text-muted-foreground">
                          <span className="font-medium">Why this job needs it:</span> {gap.job_requirement_reason}
                        </p>
                      )}
                      {gap.current_resume_evidence && (
                        <p className="text-xs text-muted-foreground">
                          <span className="font-medium">Your resume today:</span> {gap.current_resume_evidence}
                        </p>
                      )}
                      <div className="space-y-2 text-sm">
                        {gap.learning_approach && (
                          <p className="leading-relaxed">
                            <span className="font-medium">How to learn:</span> {gap.learning_approach}
                          </p>
                        )}
                        {gap.suggested_project && (
                          <p className="leading-relaxed">
                            <span className="font-medium">Suggested project:</span> {gap.suggested_project}
                          </p>
                        )}
                      </div>
                      {gap.estimated_learning_duration && (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
                          ~{gap.estimated_learning_duration}
                        </span>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Evidence */}
          {match.resume_evidence.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Resume evidence used</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-inside list-disc space-y-1.5 text-sm text-muted-foreground">
                  {match.resume_evidence.map((evidence, i) => (
                    <li key={i}>{evidence}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Next steps */}
          <Card className="border-primary/30 bg-accent/40">
            <CardContent className="flex flex-wrap items-center justify-between gap-4 p-6">
              <div>
                <p className="font-semibold">Next steps</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Improve your resume bullets or practice the interview for this role.
                </p>
              </div>
              <div className="flex gap-2">
                <Button asChild variant="outline">
                  <a href="/optimizer">Open optimizer</a>
                </Button>
                <Button asChild>
                  <a href="/interview">Practice interview</a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
