import { useMemo, useState } from "react"
import { toast } from "sonner"
import {
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  Lightbulb,
  ListChecks,
  MessagesSquare,
  Send,
  XCircle,
} from "lucide-react"
import * as apiClient from "@/services/api"
import { errMessage } from "@/services/api"
import { useApp } from "@/store/AppContext"
import {
  ALL_CATEGORIES,
  type AnswerEvaluation,
  type Difficulty,
  type QuestionCategory,
  type StoredInterviewQuestion,
} from "@/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { EmptyState } from "@/components/EmptyState"
import { MethodBadge } from "@/components/MethodBadge"
import { SkillChip } from "@/components/SkillChip"
import { cn } from "@/lib/utils"

const CATEGORY_LABELS: Record<QuestionCategory, string> = {
  technical: "Technical",
  programming: "Programming",
  project: "Project",
  hr: "HR",
  behavioral: "Behavioral",
  scenario: "Scenario",
}

export default function Interview() {
  const { resumes, jobs, activeResumeId, activeJobId, setActiveResume, setActiveJob } = useApp()
  const [categories, setCategories] = useState<QuestionCategory[]>(["technical", "project", "hr"])
  const [difficultyFilter, setDifficultyFilter] = useState<string>("all")
  const [loading, setLoading] = useState(false)
  const [questions, setQuestions] = useState<StoredInterviewQuestion[]>([])
  const [note, setNote] = useState<string | null>(null)
  const [method, setMethod] = useState<"gemini" | "glm_bridge" | "rule_based" | null>(null)
  const [openIndex, setOpenIndex] = useState<number | null>(null)
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [evaluations, setEvaluations] = useState<Record<number, AnswerEvaluation>>({})
  const [evaluating, setEvaluating] = useState<number | null>(null)

  const toggleCategory = (category: QuestionCategory) => {
    setCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category],
    )
  }

  const generate = async () => {
    if (!activeResumeId) {
      toast.error("Select a resume first")
      return
    }
    if (categories.length === 0) {
      toast.error("Select at least one category")
      return
    }
    setLoading(true)
    setQuestions([])
    setAnswers({})
    setEvaluations({})
    setOpenIndex(null)
    try {
      const response = await apiClient.generateInterviewQuestions(
        activeResumeId,
        activeJobId,
        categories,
        5,
      )
      setQuestions(response.questions)
      setNote(response.note ?? null)
      setMethod(response.method)
      toast.success(`${response.questions.length} question(s) generated`)
    } catch (error) {
      toast.error("Generation failed", { description: errMessage(error) })
    } finally {
      setLoading(false)
    }
  }

  const filtered = useMemo(() => {
    if (difficultyFilter === "all") return questions
    return questions.filter((q) => q.difficulty === difficultyFilter)
  }, [questions, difficultyFilter])

  const submitAnswer = async (index: number) => {
    const question = filtered[index]
    const answer = answers[question.id]?.trim()
    if (!answer || answer.length < 20) {
      toast.error("Write a longer answer first", { description: "At least a couple of sentences." })
      return
    }
    setEvaluating(question.id)
    try {
      const response = await apiClient.evaluateAnswer(
        question.question,
        answer,
        activeResumeId,
        activeJobId,
      )
      setEvaluations((prev) => ({ ...prev, [question.id]: response.evaluation }))
      toast.success("Feedback ready")
    } catch (error) {
      toast.error("Evaluation failed", { description: errMessage(error) })
    } finally {
      setEvaluating(null)
    }
  }

  const difficultyTone = (difficulty: Difficulty) =>
    difficulty === "hard" ? "danger" : difficulty === "medium" ? "warning" : "success"

  return (
    <div className="space-y-8">
      {/* Controls */}
      <Card>
        <CardContent className="space-y-4 p-6">
          <div className="flex flex-col gap-4 sm:flex-row">
            <div className="flex-1">
              <label htmlFor="int-resume" className="mb-1.5 block text-sm font-medium">
                Resume
              </label>
              <Select
                value={activeResumeId ? String(activeResumeId) : undefined}
                onValueChange={(v) => setActiveResume(Number(v))}
              >
                <SelectTrigger id="int-resume" className="w-full">
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
              <label htmlFor="int-job" className="mb-1.5 block text-sm font-medium">
                Target job <span className="text-muted-foreground">(optional)</span>
              </label>
              <Select
                value={activeJobId ? String(activeJobId) : undefined}
                onValueChange={(v) => setActiveJob(Number(v))}
              >
                <SelectTrigger id="int-job" className="w-full">
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
          </div>

          <div>
            <p className="mb-2 text-sm font-medium">Categories</p>
            <div className="flex flex-wrap gap-2">
              {ALL_CATEGORIES.map((category) => {
                const active = categories.includes(category)
                return (
                  <button
                    key={category}
                    type="button"
                    onClick={() => toggleCategory(category)}
                    aria-pressed={active}
                    className={cn(
                      "rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
                      active
                        ? "border-primary bg-primary text-primary-foreground shadow-sm"
                        : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-foreground",
                    )}
                  >
                    {CATEGORY_LABELS[category]}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <label htmlFor="difficulty-filter" className="text-sm font-medium">
                Difficulty
              </label>
              <Select value={difficultyFilter} onValueChange={setDifficultyFilter}>
                <SelectTrigger id="difficulty-filter" className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => void generate()} disabled={loading || !activeResumeId} size="lg">
              {loading ? "Generating..." : "Generate questions"}
              {!loading && <MessagesSquare className="size-4" aria-hidden />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {resumes.length === 0 && !loading && (
        <EmptyState
          icon={BrainCircuit}
          title="No resume selected"
          description="Upload a resume so the agent can generate questions grounded in your actual projects and skills."
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
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-4 w-2/3" />
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

      {method && questions.length > 0 && (
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">
            {filtered.length} question(s) shown - click a question to expand
          </p>
          <MethodBadge method={method} />
        </div>
      )}

      <div className="space-y-4">
        {filtered.map((question, index) => {
          const open = openIndex === index
          const evaluation = evaluations[question.id]
          return (
            <Card key={question.id}>
              <CardContent className="p-0">
                <button
                  type="button"
                  onClick={() => setOpenIndex(open ? null : index)}
                  aria-expanded={open}
                  className="flex w-full items-start justify-between gap-4 p-5 text-left transition-colors hover:bg-slate-50/70"
                >
                  <div className="min-w-0 flex-1">
                    <div className="mb-1.5 flex flex-wrap items-center gap-2">
                      <SkillChip label={CATEGORY_LABELS[question.category]} tone="info" />
                      <SkillChip label={question.difficulty} tone={difficultyTone(question.difficulty)} />
                    </div>
                    <p className="font-medium leading-relaxed">{question.question}</p>
                  </div>
                  <ChevronDown
                    className={cn(
                      "mt-1 size-5 shrink-0 text-muted-foreground transition-transform",
                      open && "rotate-180",
                    )}
                    aria-hidden
                  />
                </button>

                {open && (
                  <div className="space-y-5 border-t px-5 py-5">
                    {question.why_asked && (
                      <div className="flex gap-2.5">
                        <Lightbulb className="mt-0.5 size-4 shrink-0 text-amber-500" aria-hidden />
                        <p className="text-sm leading-relaxed text-muted-foreground">
                          <span className="font-medium text-foreground">Why it is asked:</span>{" "}
                          {question.why_asked}
                        </p>
                      </div>
                    )}

                    {question.key_concepts.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5">
                        <ListChecks className="size-4 text-muted-foreground" aria-hidden />
                        <span className="text-sm font-medium">Key concepts:</span>
                        {question.key_concepts.map((concept) => (
                          <SkillChip key={concept} label={concept} />
                        ))}
                      </div>
                    )}

                    {question.answer_structure && (
                      <div className="rounded-lg bg-slate-50 p-3">
                        <p className="text-sm font-medium">Suggested answer structure</p>
                        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                          {question.answer_structure}
                        </p>
                      </div>
                    )}

                    {/* Practice answer */}
                    <div className="space-y-2.5">
                      <label htmlFor={`answer-${question.id}`} className="text-sm font-medium">
                        Practice your answer
                      </label>
                      <Textarea
                        id={`answer-${question.id}`}
                        placeholder="Type your answer as you would say it in the interview - the AI coach will score relevance, clarity, technical accuracy and completeness..."
                        value={answers[question.id] ?? ""}
                        onChange={(e) =>
                          setAnswers((prev) => ({ ...prev, [question.id]: e.target.value }))
                        }
                        rows={5}
                        className="resize-y"
                      />
                      <div className="flex items-center gap-3">
                        <Button
                          size="sm"
                          onClick={() => void submitAnswer(index)}
                          disabled={evaluating === question.id}
                        >
                          {evaluating === question.id ? "Evaluating..." : "Get AI feedback"}
                          {evaluating !== question.id && <Send className="size-4" aria-hidden />}
                        </Button>
                        <p className="text-xs text-muted-foreground">
                          Requires an AI provider (Gemini or the local bridge).
                        </p>
                      </div>
                    </div>

                    {evaluation && (
                      <div className="space-y-4 rounded-lg border border-primary/30 bg-accent/30 p-4">
                        <div>
                          <p className="text-sm font-semibold">AI coach feedback</p>
                          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                            {evaluation.overall_feedback}
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                          {[
                            ["Relevance", evaluation.relevance_score],
                            ["Clarity", evaluation.clarity_score],
                            ["Technical", evaluation.technical_accuracy_score],
                            ["Completeness", evaluation.completeness_score],
                          ].map(([label, value]) => (
                            <div key={label as string} className="rounded-lg bg-white p-3 text-center shadow-sm">
                              <p className="text-lg font-bold text-primary">{value}</p>
                              <p className="text-[11px] text-muted-foreground">{label}</p>
                            </div>
                          ))}
                        </div>
                        <div className="grid gap-4 sm:grid-cols-2">
                          {evaluation.strengths.length > 0 && (
                            <div>
                              <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
                                <CheckCircle2 className="size-3.5" aria-hidden /> Strengths
                              </p>
                              <ul className="list-inside list-disc space-y-1 text-xs text-muted-foreground">
                                {evaluation.strengths.map((strength, i) => (
                                  <li key={i}>{strength}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {evaluation.improvements.length > 0 && (
                            <div>
                              <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-amber-700">
                                <XCircle className="size-3.5" aria-hidden /> Improvements
                              </p>
                              <ul className="list-inside list-disc space-y-1 text-xs text-muted-foreground">
                                {evaluation.improvements.map((improvement, i) => (
                                  <li key={i}>{improvement}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                        {evaluation.suggested_answer_outline && (
                          <div className="rounded-lg bg-white p-3">
                            <p className="text-xs font-semibold">Model answer outline</p>
                            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                              {evaluation.suggested_answer_outline}
                            </p>
                          </div>
                        )}
                        <p className="text-[11px] text-muted-foreground">{evaluation.disclaimer}</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
