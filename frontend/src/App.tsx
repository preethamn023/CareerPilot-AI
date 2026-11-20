import { Route, Routes } from "react-router-dom"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import Dashboard from "@/pages/Dashboard"
import History from "@/pages/History"
import Interview from "@/pages/Interview"
import JobAnalyzer from "@/pages/JobAnalyzer"
import Landing from "@/pages/Landing"
import MatchAnalysis from "@/pages/MatchAnalysis"
import Optimizer from "@/pages/Optimizer"
import ResumeUpload from "@/pages/ResumeUpload"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<DashboardLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/resume" element={<ResumeUpload />} />
        <Route path="/jobs" element={<JobAnalyzer />} />
        <Route path="/match" element={<MatchAnalysis />} />
        <Route path="/optimizer" element={<Optimizer />} />
        <Route path="/interview" element={<Interview />} />
        <Route path="/history" element={<History />} />
      </Route>
      <Route
        path="*"
        element={
          <div className="flex min-h-screen items-center justify-center bg-background">
            <div className="text-center">
              <h1 className="text-2xl font-bold">Page not found</h1>
              <a href="/" className="mt-3 inline-block text-primary underline-offset-4 hover:underline">
                Back to home
              </a>
            </div>
          </div>
        }
      />
    </Routes>
  )
}
