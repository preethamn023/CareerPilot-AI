import { cn } from "@/lib/utils"

interface ScoreGaugeProps {
  score: number
  size?: number
  label?: string
  className?: string
}

/** Deterministic SVG radial gauge for the overall match score. */
export function ScoreGauge({ score, size = 176, label = "Overall match", className }: ScoreGaugeProps) {
  const clamped = Math.max(0, Math.min(100, score))
  const stroke = 12
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - clamped / 100)

  const color =
    clamped >= 75 ? "#16a34a" : clamped >= 50 ? "#2563eb" : clamped >= 30 ? "#d97706" : "#dc2626"

  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${label}: ${clamped} out of 100`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        <text
          x="50%"
          y="47%"
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={size * 0.26}
          fontWeight={700}
          fill="#0f172a"
        >
          {clamped}
        </text>
        <text
          x="50%"
          y="64%"
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={size * 0.085}
          fill="#64748b"
        >
          / 100
        </text>
      </svg>
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
    </div>
  )
}
