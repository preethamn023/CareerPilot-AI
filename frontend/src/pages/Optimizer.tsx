import { useState } from "react"
import { toast } from "sonner"
import { Check, Copy, Sparkles, WandSparkles } from "lucide-react"
import * as apiClient from "@/services/api"
import { errMessage } from "@/services/api"
import { useApp } from "@/store/AppContext"
import type { BulletOptimization as BulletOptimizationType } from "@/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
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
import { SkillChip } from "@/components/SkillChip"

export default function Optimizer() {
  const { resumes, jobs, activeResumeId, activeJobId, setActiveResume, setActiveJob } = useApp()
  const [loading, setLoading] = useState(false)
  const [optimizations, setOptimizations] = useState<BulletOptimizationType[]>([])
  const [note, setNote] = useState<string | null>(null)
  const [method, setMethod] = useState<"gemini" | "glm_bridge" | "rule_based" | null>(null)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  const optimize = async () => {
    if (!activeResumeId) {
      toast.error("Select a resume first")
      return
    }
    setLoading(true)
    setOptimizations([])
    setSelected(new Set())
    try {
      const response = await apiClient.optimizeBullets(activeResumeId, activeJobId)
      setOptimizations(response.optimizations)
      setNote(response.note ?? null)
      setMethod(response.method)
      if (response.optimizations.length === 0) {
        toast.info("No bullet points found to optimize", {
          description: "Your resume may not have enough project or experience descriptions.",
        })
      } else {
        toast.success(`${response.optimizations.length} suggestions generated`)
      }
    } catch (error) {
      toast.error("Optimization failed", { description: errMessage(error) })
    } finally {
      setLoading(false)
    }
  }

  const toggle = (index: number, checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (checked) next.add(index)
      else next.delete(index)
      return next
    })
  }

  const copyText = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedIndex(index)
      toast.success("Copied to clipboard")
      setTimeout(() => setCopiedIndex(null), 1500)
    } catch {
      toast.error("Could not copy - your browser blocked clipboard access")
    }
  }

  const copySelected = async () => {
    const chosen = optimizations.filter((_, i) => selected.has(i))
    if (chosen.length === 0) {
      toast.error("Select at least one suggestion first")
      return
    }
    const text = chosen.map((o) => o.optimized_bullet).join("\n")
    await copyText(text, -2)
    toast.success(`${chosen.length} bullet(s) copied`)
  }

  return (
    <div className="space-y-8">
      {/* Controls */}
      <Card>
        <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="opt-resume" className="mb-1.5 block text-sm font-medium">
              Resume
            </label>
            <Select
              value={activeResumeId ? String(activeResumeId) : undefined}
              onValueChange={(v) => setActiveResume(Number(v))}
            >
              <SelectTrigger id="opt-resume" className="w-full">
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
            <label htmlFor="opt-job" className="mb-1.5 block text-sm font-medium">
              Target job <span className="text-muted-foreground">(optional - improves relevance)</span>
            </label>
            <Select
              value={activeJobId ? String(activeJobId) : undefined}
              onValueChange={(v) => setActiveJob(Number(v))}
            >
              <SelectTrigger id="opt-job" className="w-full">
                <SelectValue placeholder="No target job" />
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
          <Button onClick={() => void optimize()} disabled={loading || !activeResumeId} size="lg">
            {loading ? "Optimizing..." : "Generate suggestions"}
            {!loading && <WandSparkles className="size-4" aria-hidden />}
          </Button>
        </CardContent>
      </Card>

      {resumes.length === 0 && !loading && (
        <EmptyState
          icon={Sparkles}
          title="No resume selected"
          description="Upload a resume first - the optimizer rewrites bullet points that already exist in it."
          action={
            <Button asChild size="sm">
              <a href="/resume">Upload resume</a>
            </Button>
          }
        />
      )}

      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="space-y-3 p-6">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {note && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
          {note}
        </div>
      )}

      {method && optimizations.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <p className="text-sm font-medium text-muted-foreground">
              {optimizations.length} suggestion(s) - {selected.size} selected
            </p>
            <MethodBadge method={method} />
          </div>
          <Button variant="outline" size="sm" onClick={() => void copySelected()}>
            <Copy className="size-4" aria-hidden /> Copy selected
          </Button>
        </div>
      )}

      <div className="space-y-4">
        {optimizations.map((opt, index) => (
          <Card key={index}>
            <CardContent className="space-y-4 p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Checkbox
                    id={`opt-${index}`}
                    checked={selected.has(index)}
                    onCheckedChange={(checked) => toggle(index, checked === true)}
                    aria-label={`Select suggestion ${index + 1}`}
                  />
                  <label htmlFor={`opt-${index}`} className="cursor-pointer text-sm font-medium capitalize">
                    {opt.section.replace("_", " ")}
                  </label>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => void copyText(opt.optimized_bullet, index)}
                  aria-label="Copy optimized bullet"
                >
                  {copiedIndex === index ? (
                    <>
                      <Check className="size-4" aria-hidden /> Copied
                    </>
                  ) : (
                    <>
                      <Copy className="size-4" aria-hidden /> Copy
                    </>
                  )}
                </Button>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border bg-slate-50/70 p-4">
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Original
                  </p>
                  <p className="text-sm leading-relaxed text-slate-600 line-through decoration-slate-300">
                    {opt.original_bullet}
                  </p>
                </div>
                <div className="rounded-lg border border-primary/30 bg-accent/40 p-4">
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-primary">
                    Optimized
                  </p>
                  <p className="text-sm font-medium leading-relaxed">{opt.optimized_bullet}</p>
                </div>
              </div>

              <div>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  <span className="font-medium text-foreground">Why it is better:</span>{" "}
                  {opt.improvement_rationale}
                </p>
                {opt.keywords_highlighted.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                    <span className="text-xs text-muted-foreground">Keywords highlighted:</span>
                    {opt.keywords_highlighted.map((keyword) => (
                      <SkillChip key={keyword} label={keyword} tone="info" />
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {optimizations.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Every suggestion rewrites only information already present in your resume. Metrics,
          internships or achievements are never invented - if the original bullet has no numbers,
          the rewrite keeps it that way.
        </p>
      )}
    </div>
  )
}
