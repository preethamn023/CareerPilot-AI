import { useState } from "react"
import { toast } from "sonner"
import { Building2, CheckCircle2, Globe, Link2, Trash2 } from "lucide-react"
import * as apiClient from "@/services/api"
import { errMessage } from "@/services/api"
import { useApp } from "@/store/AppContext"
import type { JobResponse } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { MethodBadge } from "@/components/MethodBadge"
import { SkillChip } from "@/components/SkillChip"

export default function JobAnalyzer() {
  const { jobs, activeJobId, setActiveJob, refreshData } = useApp()
  const [url, setUrl] = useState("")
  const [text, setText] = useState("")
  const [title, setTitle] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<JobResponse | null>(null)
  const [loadingExisting, setLoadingExisting] = useState(false)

  const analyzeUrl = async () => {
    if (!url.trim()) {
      toast.error("Enter a job description URL")
      return
    }
    setLoading(true)
    setResult(null)
    try {
      const response = await apiClient.analyzeJobFromUrl(url.trim())
      setResult(response)
      setActiveJob(response.id)
      await refreshData()
      toast.success("Job analysed from URL", {
        description: `${response.job.role ?? "Role"}${response.job.company ? ` at ${response.job.company}` : ""}`,
      })
    } catch (error) {
      toast.error("Could not analyse this URL", { description: errMessage(error) })
    } finally {
      setLoading(false)
    }
  }

  const analyzeText = async () => {
    if (text.trim().length < 80) {
      toast.error("Job description too short", {
        description: "Paste the full job description (at least 80 characters).",
      })
      return
    }
    setLoading(true)
    setResult(null)
    try {
      const response = await apiClient.analyzeJobFromText(text.trim(), title.trim() || undefined)
      setResult(response)
      setActiveJob(response.id)
      await refreshData()
      toast.success("Job description analysed")
    } catch (error) {
      toast.error("Analysis failed", { description: errMessage(error) })
    } finally {
      setLoading(false)
    }
  }

  const loadExisting = async (id: number) => {
    setLoadingExisting(true)
    setActiveJob(id)
    try {
      setResult(await apiClient.getJob(id))
    } catch (error) {
      toast.error("Could not load job", { description: errMessage(error) })
    } finally {
      setLoadingExisting(false)
    }
  }

  const removeJob = async (id: number) => {
    try {
      await apiClient.deleteJob(id)
      if (activeJobId === id) setActiveJob(null)
      if (result?.id === id) setResult(null)
      await refreshData()
      toast.success("Job deleted")
    } catch (error) {
      toast.error("Delete failed", { description: errMessage(error) })
    }
  }

  const info = result?.job

  return (
    <div className="space-y-8">
      <Card>
        <CardContent className="p-6">
          <Tabs defaultValue="text">
            <TabsList className="mb-4">
              <TabsTrigger value="text" className="gap-1.5">
                <Building2 className="size-4" aria-hidden /> Paste text
              </TabsTrigger>
              <TabsTrigger value="url" className="gap-1.5">
                <Globe className="size-4" aria-hidden /> From URL
              </TabsTrigger>
            </TabsList>

            <TabsContent value="text" className="space-y-4">
              <div>
                <label htmlFor="job-title" className="mb-1.5 block text-sm font-medium">
                  Job title <span className="text-muted-foreground">(optional)</span>
                </label>
                <Input
                  id="job-title"
                  placeholder="e.g. Software Engineer (Fresher)"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="job-text" className="mb-1.5 block text-sm font-medium">
                  Job description
                </label>
                <Textarea
                  id="job-text"
                  placeholder="Paste the complete job description here - responsibilities, requirements, skills, qualifications..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={10}
                  className="resize-y"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  {text.trim().length.toLocaleString()} characters (minimum 80)
                </p>
              </div>
              <Button onClick={() => void analyzeText()} disabled={loading}>
                {loading ? "Analysing..." : "Analyse job description"}
              </Button>
            </TabsContent>

            <TabsContent value="url" className="space-y-4">
              <div>
                <label htmlFor="job-url" className="mb-1.5 block text-sm font-medium">
                  Job posting URL
                </label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Link2 className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
                    <Input
                      id="job-url"
                      placeholder="https://example.com/careers/software-engineer"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      className="pl-9"
                      inputMode="url"
                    />
                  </div>
                  <Button onClick={() => void analyzeUrl()} disabled={loading}>
                    {loading ? "Fetching..." : "Fetch & analyse"}
                  </Button>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Only public http/https pages. Sites with CAPTCHAs, logins or heavy JavaScript
                  rendering may fail - paste the text instead.
                </p>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Stored jobs */}
      {jobs.length > 0 && (
        <section>
          <h3 className="mb-3 text-base font-semibold">Analysed jobs</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <div
                key={job.id}
                className={`flex items-center justify-between gap-3 rounded-xl border bg-card p-4 shadow-sm ${
                  activeJobId === job.id ? "border-primary" : ""
                }`}
              >
                <button
                  type="button"
                  className="min-w-0 flex-1 text-left"
                  onClick={() => void loadExisting(job.id)}
                >
                  <p className="truncate text-sm font-medium">{job.role ?? `Job #${job.id}`}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {job.company ?? job.url ?? "Manual input"} - {new Date(job.created_at).toLocaleDateString()}
                  </p>
                </button>
                <div className="flex shrink-0 items-center gap-1">
                  {activeJobId === job.id && <CheckCircle2 className="size-4 text-primary" aria-label="Active job" />}
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Delete job ${job.id}`}
                    onClick={() => void removeJob(job.id)}
                  >
                    <Trash2 className="size-4 text-muted-foreground" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {loadingExisting && (
        <Card>
          <CardContent className="space-y-3 p-6">
            <Skeleton className="h-6 w-56" />
            <Skeleton className="h-4 w-80" />
            <Skeleton className="h-4 w-64" />
          </CardContent>
        </Card>
      )}

      {/* Result */}
      {info && result && (
        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
            <CardTitle className="text-lg">{info.role ?? "Job description"}</CardTitle>
            <MethodBadge method={result.extraction_method} />
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-wrap gap-2">
              {info.company && <Badge variant="secondary">{info.company}</Badge>}
              {info.location && <Badge variant="secondary">{info.location}</Badge>}
              {info.employment_type && <Badge variant="secondary">{info.employment_type}</Badge>}
              {info.experience_requirements && <Badge variant="secondary">{info.experience_requirements}</Badge>}
              {info.salary_range && <Badge variant="secondary">{info.salary_range}</Badge>}
            </div>

            {info.education_requirements && (
              <div>
                <h4 className="mb-1 text-sm font-semibold">Education requirement</h4>
                <p className="text-sm text-muted-foreground">{info.education_requirements}</p>
              </div>
            )}

            {info.required_skills.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Required skills</h4>
                <div className="flex flex-wrap gap-1.5">
                  {info.required_skills.map((skill) => (
                    <SkillChip key={skill} label={skill} tone="info" />
                  ))}
                </div>
              </div>
            )}

            {info.preferred_skills.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Preferred skills (nice to have)</h4>
                <div className="flex flex-wrap gap-1.5">
                  {info.preferred_skills.map((skill) => (
                    <SkillChip key={skill} label={skill} tone="neutral" />
                  ))}
                </div>
              </div>
            )}

            {info.responsibilities.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Responsibilities</h4>
                <ul className="list-inside list-disc space-y-1.5 text-sm text-muted-foreground">
                  {info.responsibilities.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {info.qualifications.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Qualifications</h4>
                <ul className="list-inside list-disc space-y-1.5 text-sm text-muted-foreground">
                  {info.qualifications.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {info.required_skills.length === 0 && info.responsibilities.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No structured details could be extracted from this job description.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
