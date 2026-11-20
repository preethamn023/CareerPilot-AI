import { cn } from "@/lib/utils"

type Tone = "neutral" | "success" | "warning" | "danger" | "info"

const TONES: Record<Tone, string> = {
  neutral: "bg-secondary text-secondary-foreground border-border",
  success: "bg-emerald-50 text-emerald-700 border-emerald-200",
  warning: "bg-amber-50 text-amber-700 border-amber-200",
  danger: "bg-red-50 text-red-700 border-red-200",
  info: "bg-blue-50 text-blue-700 border-blue-200",
}

export function SkillChip({
  label,
  tone = "neutral",
  title,
  className,
}: {
  label: string
  tone?: Tone
  title?: string
  className?: string
}) {
  return (
    <span
      title={title}
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        TONES[tone],
        className,
      )}
    >
      {label}
    </span>
  )
}
