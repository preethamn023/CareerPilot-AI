import { useCallback, useRef, useState } from "react"
import { toast } from "sonner"
import { CheckCircle2, CloudUpload, FileText, Mail, MapPin, Phone, Trash2, User } from "lucide-react"
import * as apiClient from "@/services/api"
import { errMessage } from "@/services/api"
import { useApp } from "@/store/AppContext"
import type { ResumeResponse } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { MethodBadge } from "@/components/MethodBadge"
import { SkillChip } from "@/components/SkillChip"

const MAX_MB = 5
const ACCEPTED = "application/pdf,.pdf"

export default function ResumeUpload() {
  const { resumes, activeResumeId, setActiveResume, refreshData } = useApp()
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<ResumeResponse | null>(null)
  const [loadingExisting, setLoadingExisting] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        toast.error("Only PDF files are accepted", {
          description: "Please export your resume as a text-based PDF.",
        })
        return
      }
      if (file.size > MAX_MB * 1024 * 1024) {
        toast.error(`File too large (max ${MAX_MB} MB)`, {
          description: "Try compressing your PDF before uploading.",
        })
        return
      }
      setUploading(true)
      setProgress(15)
      setResult(null)
      const timer = setInterval(() => setProgress((p) => Math.min(p + 5, 90)), 400)
      try {
        const response = await apiClient.uploadResume(file)
        setProgress(100)
        setResult(response)
        setActiveResume(response.id)
        await refreshData()
        toast.success("Resume analysed", {
          description: `${response.profile?.full_name ?? "Profile"} extracted (${response.char_count.toLocaleString()} characters).`,
        })
      } catch (error) {
        toast.error("Upload failed", { description: errMessage(error) })
      } finally {
        clearInterval(timer)
        setUploading(false)
        setTimeout(() => setProgress(0), 800)
      }
    },
    [refreshData, setActiveResume],
  )

  const loadExisting = async (id: number) => {
    setLoadingExisting(true)
    setActiveResume(id)
    try {
      setResult(await apiClient.getResume(id))
    } catch (error) {
      toast.error("Could not load resume", { description: errMessage(error) })
    } finally {
      setLoadingExisting(false)
    }
  }

  const removeResume = async (id: number) => {
    try {
      await apiClient.deleteResume(id)
      if (activeResumeId === id) setActiveResume(null)
      if (result?.id === id) setResult(null)
      await refreshData()
      toast.success("Resume deleted")
    } catch (error) {
      toast.error("Delete failed", { description: errMessage(error) })
    }
  }

  const profile = result?.profile

  return (
    <div className="space-y-8">
      {/* Drop zone */}
      <Card>
        <CardContent className="p-6">
          <div
            role="button"
            tabIndex={0}
            aria-label="Upload resume PDF"
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") inputRef.current?.click()
            }}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragging(false)
              const file = e.dataTransfer.files?.[0]
              if (file) void handleFile(file)
            }}
            className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors ${
              dragging
                ? "border-primary bg-accent"
                : "border-border hover:border-primary/50 hover:bg-accent/40"
            }`}
          >
            <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
              <CloudUpload className="size-7" aria-hidden />
            </div>
            <div>
              <p className="font-semibold">
                {uploading ? "Analysing your resume..." : "Drag & drop your resume PDF here"}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                or click to browse - PDF only, max {MAX_MB} MB, text-based (not scanned)
              </p>
            </div>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED}
              className="sr-only"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) void handleFile(file)
                e.target.value = ""
              }}
            />
          </div>
          {progress > 0 && (
            <div className="mt-4 space-y-1.5">
              <Progress value={progress} aria-label="Upload progress" />
              <p className="text-xs text-muted-foreground">
                {progress < 100
                  ? "Extracting text and structuring your profile with the extraction agent..."
                  : "Done"}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stored resumes */}
      {resumes.length > 0 && (
        <section>
          <h3 className="mb-3 text-base font-semibold">Your resumes</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {resumes.map((resume) => (
              <div
                key={resume.id}
                className={`flex items-center justify-between gap-3 rounded-xl border bg-card p-4 shadow-sm ${
                  activeResumeId === resume.id ? "border-primary" : ""
                }`}
              >
                <button
                  type="button"
                  className="flex min-w-0 flex-1 items-center gap-3 text-left"
                  onClick={() => void loadExisting(resume.id)}
                >
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <FileText className="size-5" aria-hidden />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{resume.filename}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {resume.full_name ?? "Unknown candidate"} - {new Date(resume.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </button>
                <div className="flex shrink-0 items-center gap-1">
                  {activeResumeId === resume.id && <CheckCircle2 className="size-4 text-primary" aria-label="Active resume" />}
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Delete ${resume.filename}`}
                    onClick={() => void removeResume(resume.id)}
                  >
                    <Trash2 className="size-4 text-muted-foreground" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Extracted profile */}
      {loadingExisting && (
        <Card>
          <CardContent className="space-y-3 p-6">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-72" />
            <Skeleton className="h-4 w-64" />
          </CardContent>
        </Card>
      )}

      {result && profile && (
        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
            <CardTitle className="text-lg">Extracted profile</CardTitle>
            <MethodBadge method={result.extraction_method} />
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Identity */}
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xl font-bold">{profile.full_name ?? "Name not detected"}</p>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1.5 text-sm text-muted-foreground">
                  {profile.email && (
                    <span className="inline-flex items-center gap-1.5">
                      <Mail className="size-3.5" aria-hidden /> {profile.email}
                    </span>
                  )}
                  {profile.phone && (
                    <span className="inline-flex items-center gap-1.5">
                      <Phone className="size-3.5" aria-hidden /> {profile.phone}
                    </span>
                  )}
                  {profile.location && (
                    <span className="inline-flex items-center gap-1.5">
                      <MapPin className="size-3.5" aria-hidden /> {profile.location}
                    </span>
                  )}
                </div>
              </div>
              <Badge variant="secondary" className="gap-1.5">
                <User className="size-3.5" aria-hidden />
                {result.page_count} page(s) - {result.char_count.toLocaleString()} characters
              </Badge>
            </div>

            {profile.professional_summary && (
              <div>
                <h4 className="mb-1.5 text-sm font-semibold">Summary</h4>
                <p className="text-sm leading-relaxed text-muted-foreground">{profile.professional_summary}</p>
              </div>
            )}

            {/* Skills */}
            {profile.technical_skills.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Technical skills ({profile.technical_skills.length})</h4>
                <div className="flex flex-wrap gap-1.5">
                  {profile.technical_skills.map((skill) => (
                    <SkillChip key={skill} label={skill} tone="info" />
                  ))}
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  {profile.programming_languages.length} languages - {profile.frameworks.length} frameworks -{" "}
                  {profile.tools_and_technologies.length} tools
                </p>
              </div>
            )}

            {/* Education */}
            {profile.education.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Education</h4>
                <div className="space-y-2">
                  {profile.education.map((edu, i) => (
                    <div key={i} className="rounded-lg border bg-slate-50/60 p-3 text-sm">
                      <p className="font-medium">{edu.degree}</p>
                      <p className="text-muted-foreground">
                        {[edu.institution, edu.year, edu.score].filter(Boolean).join(" | ")}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Projects */}
            {profile.projects.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Projects ({profile.projects.length})</h4>
                <div className="space-y-3">
                  {profile.projects.map((project, i) => (
                    <div key={i} className="rounded-lg border p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="font-medium">{project.name ?? `Project ${i + 1}`}</p>
                        <div className="flex flex-wrap gap-1">
                          {project.technologies.slice(0, 6).map((tech) => (
                            <SkillChip key={tech} label={tech} />
                          ))}
                        </div>
                      </div>
                      {project.description && (
                        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{project.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Experience */}
            {(profile.internships.length > 0 || profile.work_experience.length > 0) && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Experience</h4>
                <div className="space-y-2">
                  {[...profile.internships, ...profile.work_experience].map((item, i) => (
                    <div key={i} className="rounded-lg border bg-slate-50/60 p-3 text-sm">
                      <p className="font-medium">
                        {item.role ?? "Role"}
                        {item.organization ? ` - ${item.organization}` : ""}
                        {item.duration ? (
                          <span className="ml-2 font-normal text-muted-foreground">({item.duration})</span>
                        ) : null}
                      </p>
                      {item.description && <p className="mt-1 text-muted-foreground">{item.description}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Certifications + achievements */}
            {(profile.certifications.length > 0 || profile.achievements.length > 0) && (
              <div className="grid gap-6 md:grid-cols-2">
                {profile.certifications.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-sm font-semibold">Certifications</h4>
                    <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                      {profile.certifications.map((cert, i) => (
                        <li key={i}>{cert}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {profile.achievements.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-sm font-semibold">Achievements</h4>
                    <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                      {profile.achievements.map((achievement, i) => (
                        <li key={i}>{achievement}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <Separator />
            <p className="text-xs text-muted-foreground">
              Missing fields are shown as empty rather than guessed - the extraction agent never
              invents information. You can now analyse a job description and run a match report.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
