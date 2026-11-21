import { Link } from "react-router-dom"
import {
  ArrowRight,
  Briefcase,
  FileText,
  Gauge,
  Layers,
  MessagesSquare,
  Sparkles,
  TrendingUp,
} from "lucide-react"
import { useApp } from "@/store/AppContext"
import { METHOD_LABELS } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { EmptyState } from "@/components/EmptyState"
import { MethodBadge } from "@/components/MethodBadge"

const QUICK_ACTIONS = [
  {
    to: "/resume",
    icon: FileText,
    title: "Upload resume",
    description: "Extract a structured profile from your PDF",
  },
  {
    to: "/jobs",
    icon: Briefcase,
    title: "Analyse a job",
    description: "Paste text or use a public job URL",
  },
  {
    to: "/match",
    icon: Gauge,
    title: "Run match analysis",
    description: "Explainable compatibility report",
  },
  {
    to: "/interview",
    icon: MessagesSquare,
    title: "Practice interview",
    description: "Personalised questions and feedback",
  },
]

export default function Dashboard() {
  const { resumes, jobs, history, health, activeResumeId } = useApp()

  const latestAnalysis = history[0]
  const activeResume = resumes.find((r) => r.id === activeResumeId)

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <section>
        <h2 className="text-2xl font-bold tracking-tight">
          {activeResume?.full_name ? `Welcome back, ${activeResume.full_name.split(" ")[0]}` : "Welcome to CareerPilot AI"}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {resumes.length === 0
            ? "Start by uploading your resume, then analyse a target job description."
            : "Track your job readiness and keep improving your preparation."}
        </p>
      </section>

      {/* Stats */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Statistics">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">Resume</p>
              <FileText className="size-4 text-muted-foreground" aria-hidden />
            </div>
            {health ? (
              <>
                <p className="mt-2 text-2xl font-bold">
                  {resumes.length > 0 ? "Ready" : "Not uploaded"}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {activeResume
                    ? `${activeResume.filename} (${activeResume.char_count.toLocaleString()} chars)`
                    : resumes.length > 0
                      ? `${resumes.length} resume(s) stored`
                      : "Upload a PDF to begin"}
                </p>
              </>
            ) : (
              <Skeleton className="mt-2 h-8 w-28" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">Latest match score</p>
              <TrendingUp className="size-4 text-muted-foreground" aria-hidden />
            </div>
            {latestAnalysis ? (
              <>
                <p className="mt-2 text-2xl font-bold">
                  {latestAnalysis.overall_match_score}
                  <span className="text-sm font-medium text-muted-foreground"> / 100</span>
                </p>
                <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">
                  {latestAnalysis.job_role ?? "Job"} {latestAnalysis.company ? `at ${latestAnalysis.company}` : ""}
                </p>
              </>
            ) : (
              <>
                <p className="mt-2 text-2xl font-bold text-muted-foreground">-</p>
                <p className="mt-1 text-xs text-muted-foreground">Run a match analysis first</p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">Jobs analysed</p>
              <Briefcase className="size-4 text-muted-foreground" aria-hidden />
            </div>
            <p className="mt-2 text-2xl font-bold">{jobs.length}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {jobs.length > 0 ? "Most recent: " + (jobs[0].role ?? jobs[0].url ?? "job") : "No jobs analysed yet"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">Match reports</p>
              <Layers className="size-4 text-muted-foreground" aria-hidden />
            </div>
            <p className="mt-2 text-2xl font-bold">{history.length}</p>
            <p className="mt-1 text-xs text-muted-foreground">Stored in your local database</p>
          </CardContent>
        </Card>
      </section>

      {/* AI engine status */}
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-3 p-5">
          <div className="flex items-center gap-3">
            <Sparkles className="size-5 text-primary" aria-hidden />
            <div>
              <p className="text-sm font-semibold">
                {health?.ai_configured
                  ? `AI engine: ${METHOD_LABELS[health.ai_provider as "gemini" | "glm_bridge"]}`
                  : "AI engine: rule-based mode"}
              </p>
              <p className="text-xs text-muted-foreground">
                {health?.ai_configured
                  ? health.ai_model
                    ? `Model: ${health.ai_model}`
                    : "Semantic analysis, optimization and interviews are fully AI-powered."
                  : "Add GEMINI_API_KEY to root .env for AI-powered analysis. Deterministic analysis still works."}
              </p>
            </div>
          </div>
          {health?.ai_configured ? (
            <Badge className="gap-1.5">
              <span className="size-1.5 rounded-full bg-emerald-400" aria-hidden /> Online
            </Badge>
          ) : (
            <Badge variant="secondary" className="gap-1.5">
              <span className="size-1.5 rounded-full bg-amber-500" aria-hidden /> Offline mode
            </Badge>
          )}
        </CardContent>
      </Card>

      {/* Recent analyses */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-semibold">Recent analyses</h3>
          <Button asChild variant="ghost" size="sm">
            <Link to="/history">
              View all
              <ArrowRight className="size-4" aria-hidden />
            </Link>
          </Button>
        </div>
        {history.length === 0 ? (
          <EmptyState
            icon={Gauge}
            title="No analyses yet"
            description="Upload a resume and analyse a job description, then run your first match analysis."
            action={
              <Button asChild size="sm">
                <Link to="/resume">Upload resume</Link>
              </Button>
            }
          />
        ) : (
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job role</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead className="text-center">Score</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.slice(0, 5).map((item) => (
                  <TableRow key={item.analysis_id}>
                    <TableCell className="font-medium">{item.job_role ?? `Job #${item.job_id}`}</TableCell>
                    <TableCell className="text-muted-foreground">{item.company ?? "-"}</TableCell>
                    <TableCell className="text-center">
                      <span
                        className={
                          item.overall_match_score >= 70
                            ? "font-semibold text-emerald-600"
                            : item.overall_match_score >= 45
                              ? "font-semibold text-blue-600"
                              : "font-semibold text-amber-600"
                        }
                      >
                        {item.overall_match_score}
                      </span>
                    </TableCell>
                    <TableCell>
                      <MethodBadge method={item.analysis_method} />
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(item.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button asChild variant="outline" size="sm">
                        <Link to={`/match?analysis=${item.analysis_id}`}>View report</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </section>

      {/* Quick actions */}
      <section>
        <h3 className="mb-3 text-base font-semibold">Quick actions</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {QUICK_ACTIONS.map((action) => (
            <Link
              key={action.to}
              to={action.to}
              className="group rounded-xl border bg-card p-5 shadow-sm transition-all hover:border-primary/40 hover:shadow-md"
            >
              <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <action.icon className="size-5" aria-hidden />
              </div>
              <p className="mt-3 font-semibold">{action.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">{action.description}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
