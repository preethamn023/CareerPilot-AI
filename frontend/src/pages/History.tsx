import { useState } from "react"
import { toast } from "sonner"
import { Eye, History as HistoryIcon, Trash2 } from "lucide-react"
import * as apiClient from "@/services/api"
import { errMessage } from "@/services/api"
import { useApp } from "@/store/AppContext"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
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

export default function History() {
  const { history, refreshData } = useApp()
  const [deleting, setDeleting] = useState<number | null>(null)

  const remove = async (id: number) => {
    setDeleting(id)
    try {
      await apiClient.deleteAnalysis(id)
      await refreshData()
      toast.success("Analysis deleted")
    } catch (error) {
      toast.error("Delete failed", { description: errMessage(error) })
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        All match reports are stored in your local SQLite database. Deleting a report also removes
        its skill gaps, optimization suggestions and interview questions.
      </p>

      {history.length === 0 ? (
        <EmptyState
          icon={HistoryIcon}
          title="No analyses yet"
          description="Run a match analysis from the Match Analysis page and it will appear here."
          action={
            <Button asChild size="sm">
              <a href="/match">Run an analysis</a>
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
              {history.map((item) => (
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
                    {new Date(item.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button asChild variant="outline" size="sm">
                        <a href={`/match?analysis=${item.analysis_id}`}>
                          <Eye className="size-4" aria-hidden /> View
                        </a>
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => void remove(item.analysis_id)}
                        disabled={deleting === item.analysis_id}
                        aria-label={`Delete analysis ${item.analysis_id}`}
                      >
                        <Trash2 className="size-4 text-red-500" aria-hidden />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  )
}
