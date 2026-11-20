import { Link } from "react-router-dom"
import {
  ArrowRight,
  BadgeCheck,
  Bot,
  BrainCircuit,
  FileSearch,
  Gauge,
  GraduationCap,
  ListChecks,
  MessagesSquare,
  PlaneTakeoff,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"

const FEATURES = [
  {
    icon: FileSearch,
    title: "Resume Intelligence",
    description:
      "Upload your PDF resume and the agent extracts a structured profile - education, skills, projects, internships - without inventing anything.",
  },
  {
    icon: Target,
    title: "Job Description Analyzer",
    description:
      "Paste a job description or a public URL. The agent identifies the company, role, required and preferred skills, responsibilities and qualifications.",
  },
  {
    icon: Gauge,
    title: "Explainable Match Score",
    description:
      "A transparent 0-100 compatibility score with sub-scores for skills, education, experience and projects - always with evidence, never a black box.",
  },
  {
    icon: ListChecks,
    title: "Skill Gap Analysis",
    description:
      "See exactly which skills the job needs that your resume lacks, with a practical learning path and a suggested project for each gap.",
  },
  {
    icon: Sparkles,
    title: "Resume Optimizer",
    description:
      "Improved bullet points with strong action verbs and relevant keywords - strictly limited to facts already in your resume. No fabrication.",
  },
  {
    icon: MessagesSquare,
    title: "Mock Interview Agent",
    description:
      "Personalised technical, project, HR and behavioral questions based on your resume and the target job, with answer structure guidance and feedback.",
  },
]

const STEPS = [
  {
    icon: FileSearch,
    title: "1. Upload your resume",
    description: "Drag and drop your PDF. Text is extracted and structured instantly.",
  },
  {
    icon: Target,
    title: "2. Add a target job",
    description: "Paste the job description or drop a public job posting URL.",
  },
  {
    icon: Gauge,
    title: "3. Get your match report",
    description: "Explainable score, matched and missing skills, and a learning plan.",
  },
  {
    icon: MessagesSquare,
    title: "4. Practice and improve",
    description: "Optimize your bullets and rehearse with a personalised mock interview.",
  },
]

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* Navbar */}
      <header className="sticky top-0 z-40 border-b bg-white/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5" aria-label="CareerPilot AI home">
            <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <PlaneTakeoff className="size-5" aria-hidden />
            </div>
            <span className="text-lg font-bold tracking-tight">CareerPilot AI</span>
          </Link>
          <nav className="hidden items-center gap-6 text-sm font-medium text-muted-foreground md:flex">
            <a href="#features" className="transition-colors hover:text-foreground">Features</a>
            <a href="#how-it-works" className="transition-colors hover:text-foreground">How it works</a>
            <a href="#trust" className="transition-colors hover:text-foreground">Why trust it</a>
          </nav>
          <Button asChild>
            <Link to="/dashboard">
              Open Dashboard
              <ArrowRight className="size-4" aria-hidden />
            </Link>
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_50%_at_50%_0%,oklch(0.93_0.03_255),transparent)]"
        />
        <div className="relative mx-auto grid max-w-6xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:items-center lg:py-24">
          <div>
            <Badge variant="secondary" className="mb-4 gap-1.5 px-3 py-1 text-xs">
              <GraduationCap className="size-3.5" aria-hidden />
              Built for campus placements
            </Badge>
            <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-5xl">
              Your AI copilot for
              <span className="text-primary"> campus placements</span>
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted-foreground">
              Upload your resume, add a target job description, and get an explainable match score,
              a skill-gap learning plan, truthful resume improvements and a personalised mock
              interview - all in one place.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to="/resume">
                  Start free analysis
                  <ArrowRight className="size-4" aria-hidden />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link to="/dashboard">View dashboard</Link>
              </Button>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              No sign-up needed. Your data stays in your local database and you can delete it anytime.
            </p>
          </div>

          {/* Hero mock card */}
          <div className="relative">
            <div className="absolute -inset-4 rounded-3xl bg-gradient-to-br from-blue-100/60 to-transparent" aria-hidden />
            <Card className="relative shadow-lg">
              <CardContent className="space-y-4 p-6">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">Match report</p>
                  <Badge variant="secondary" className="gap-1">
                    <BrainCircuit className="size-3" aria-hidden /> AI analysis
                  </Badge>
                </div>
                <div className="flex items-end gap-4">
                  <div>
                    <p className="text-5xl font-extrabold tracking-tight text-primary">72</p>
                    <p className="text-xs text-muted-foreground">overall match / 100</p>
                  </div>
                  <div className="flex-1 space-y-2 pb-1">
                    {[
                      ["Technical skills", 68],
                      ["Education", 95],
                      ["Experience", 60],
                      ["Projects", 72],
                    ].map(([name, value]) => (
                      <div key={name as string}>
                        <div className="mb-1 flex justify-between text-[11px] font-medium text-muted-foreground">
                          <span>{name}</span>
                          <span>{value}</span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full bg-primary"
                            style={{ width: `${value}%` }}
                            aria-hidden
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5 border-t pt-3">
                  <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">Python ✓ demonstrated</span>
                  <span className="rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">Docker - missing</span>
                  <span className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">React ~ partial</span>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Illustration only - your report is generated from your actual resume and job.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t bg-slate-50/70 py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">Six agents, one goal</h2>
            <p className="mt-3 text-muted-foreground">
              A modular AI agent system - each capability is a separate tool with validated inputs
              and structured outputs.
            </p>
          </div>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <Card key={feature.title} className="transition-shadow hover:shadow-md">
                <CardContent className="space-y-3 p-6">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                    <feature.icon className="size-5" aria-hidden />
                  </div>
                  <h3 className="font-semibold">{feature.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
            <p className="mt-3 text-muted-foreground">From resume to interview-ready in four steps.</p>
          </div>
          <ol className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((step) => (
              <li key={step.title} className="rounded-xl border bg-white p-6 shadow-sm">
                <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <step.icon className="size-5" aria-hidden />
                </div>
                <h3 className="mt-4 font-semibold">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.description}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Trust */}
      <section id="trust" className="border-t bg-slate-50/70 py-16">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 sm:px-6 md:grid-cols-3">
          {[
            {
              icon: ShieldCheck,
              title: "No fabrication, ever",
              text: "The agent is instructed to return null rather than invent facts. Optimized bullets only rephrase what your resume already says.",
            },
            {
              icon: BadgeCheck,
              title: "Explainable scoring",
              text: "Scores use a fixed weighted methodology computed in Python - not a mystery number. Evidence is shown for every match.",
            },
            {
              icon: Bot,
              title: "Agent architecture",
              text: "LLM tool-calling with validated Pydantic schemas. The model can never execute code, SQL or shell commands.",
            },
          ].map((item) => (
            <div key={item.title} className="flex gap-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <item.icon className="size-5" aria-hidden />
              </div>
              <div>
                <h3 className="font-semibold">{item.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{item.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-sidebar py-16">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Ready to see how ready you are?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-slate-300">
            Upload a resume and analyse a real job description in under two minutes. Everything runs
            locally - your data never leaves your machine except to the AI provider you configure.
          </p>
          <Button asChild size="lg" className="mt-8">
            <Link to="/resume">
              Get started
              <ArrowRight className="size-4" aria-hidden />
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-6 text-sm text-muted-foreground sm:flex-row sm:px-6">
          <p className="flex items-center gap-2">
            <PlaneTakeoff className="size-4" aria-hidden />
            CareerPilot AI - an open, honest placement preparation tool.
          </p>
          <p>Preparation guidance only - not an employer ATS score.</p>
        </div>
      </footer>
    </div>
  )
}
