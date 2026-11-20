import { useState } from "react"
import { NavLink, Outlet, useLocation } from "react-router-dom"
import {
  BrainCircuit,
  FileText,
  Gauge,
  History,
  Home,
  Briefcase,
  Menu,
  MessagesSquare,
  PlaneTakeoff,
  Sparkles,
  X,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useApp } from "@/store/AppContext"
import { METHOD_LABELS } from "@/types"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: Home, end: false },
  { to: "/resume", label: "Resume", icon: FileText, end: false },
  { to: "/jobs", label: "Job Analyzer", icon: Briefcase, end: false },
  { to: "/match", label: "Match Analysis", icon: Gauge, end: false },
  { to: "/optimizer", label: "Resume Optimizer", icon: Sparkles, end: false },
  { to: "/interview", label: "Interview Prep", icon: MessagesSquare, end: false },
  { to: "/history", label: "History", icon: History, end: false },
]

const TITLES: Record<string, { title: string; subtitle: string }> = {
  "/dashboard": { title: "Dashboard", subtitle: "Your placement preparation at a glance" },
  "/resume": { title: "Resume Intelligence", subtitle: "Upload your PDF resume and let the agent extract a structured profile" },
  "/jobs": { title: "Job Description Analyzer", subtitle: "Paste a job description or analyse a public job posting URL" },
  "/match": { title: "Match Analysis", subtitle: "Explainable resume-vs-job compatibility report" },
  "/optimizer": { title: "Resume Optimizer", subtitle: "Truthful bullet-point improvements grounded in your actual resume" },
  "/interview": { title: "Interview Preparation", subtitle: "Personalised mock questions and answer feedback" },
  "/history": { title: "Analysis History", subtitle: "Your previous match reports" },
}

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-1 flex-col gap-1 px-3" aria-label="Main navigation">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              isActive
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
            )
          }
        >
          <item.icon className="size-4.5 shrink-0" aria-hidden />
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5 px-5 py-6">
      <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
        <PlaneTakeoff className="size-5" aria-hidden />
      </div>
      <div className="leading-tight">
        <p className="text-sm font-bold text-white">CareerPilot AI</p>
        <p className="text-[11px] text-sidebar-foreground">Placement copilot</p>
      </div>
    </div>
  )
}

export function DashboardLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { health } = useApp()
  const meta = TITLES[location.pathname] ?? { title: "CareerPilot AI", subtitle: "" }

  const aiOnline = health?.ai_configured ?? false

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col bg-sidebar lg:flex">
        <Brand />
        <SidebarNav />
        <div className="px-5 py-5">
          <div className="rounded-lg border border-sidebar-border bg-sidebar-accent/40 p-3">
            <div className="flex items-center gap-2">
              <BrainCircuit className="size-4 text-sidebar-foreground" aria-hidden />
              <p className="text-xs font-semibold text-sidebar-accent-foreground">AI Engine</p>
            </div>
            <p className="mt-1.5 text-[11px] leading-relaxed text-sidebar-foreground">
              {health
                ? aiOnline
                  ? `${METHOD_LABELS[health.ai_provider as "gemini" | "glm_bridge"]} is active.`
                  : "Running in rule-based mode. Add GEMINI_API_KEY for full AI."
                : "Backend offline - start the FastAPI server."}
            </p>
          </div>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="sticky top-0 z-40 flex items-center justify-between border-b bg-sidebar px-4 py-3 lg:hidden">
        <Brand />
        <Button
          variant="ghost"
          size="icon"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          onClick={() => setMobileOpen((v) => !v)}
          className="text-white hover:bg-sidebar-accent"
        >
          {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </Button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 bg-sidebar lg:hidden">
          <div className="flex items-center justify-between pr-4">
            <Brand />
            <Button
              variant="ghost"
              size="icon"
              aria-label="Close menu"
              onClick={() => setMobileOpen(false)}
              className="text-white hover:bg-sidebar-accent"
            >
              <X className="size-5" />
            </Button>
          </div>
          <SidebarNav onNavigate={() => setMobileOpen(false)} />
        </div>
      )}

      {/* Main content */}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 border-b bg-background/85 backdrop-blur">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6">
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground">{meta.title}</h1>
              <p className="mt-0.5 text-sm text-muted-foreground">{meta.subtitle}</p>
            </div>
            {health && (
              <Badge variant={aiOnline ? "default" : "secondary"} className="gap-1.5">
                <span
                  className={cn("size-1.5 rounded-full", aiOnline ? "bg-emerald-400" : "bg-amber-500")}
                  aria-hidden
                />
                {aiOnline ? "AI active" : "Rule-based mode"}
              </Badge>
            )}
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
          <Outlet />
        </main>
        <footer className="border-t bg-white">
          <div className="mx-auto max-w-6xl px-4 py-5 text-xs text-muted-foreground sm:px-6">
            CareerPilot AI - preparation guidance only. Scores are explainable estimates, not employer
            ATS scores.
          </div>
        </footer>
      </div>
    </div>
  )
}
