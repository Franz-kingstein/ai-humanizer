"use client"

import { cn } from "@/lib/utils"
import { MetricChangeIcon } from "./icons"

interface MetricCardProps {
  label: string
  value: number | null | undefined
  format?: "number" | "percent" | "ratio" | "score"
  decimals?: number
  change?: number
  tooltip?: string
  className?: string
}

const formatters = {
  number: (v: number, d: number) => v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d }),
  percent: (v: number, d: number) => `${v.toFixed(d)}%`,
  ratio: (v: number, d: number) => v.toFixed(d),
  score: (v: number) => v.toFixed(1),
}

function formatChange(change: number): string {
  const sign = change > 0 ? "+" : ""
  return `${sign}${change.toFixed(2)}`
}

function getScoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400"
  if (score >= 60) return "text-amber-600 dark:text-amber-400"
  if (score >= 40) return "text-orange-600 dark:text-orange-400"
  return "text-rose-600 dark:text-rose-400"
}

function getChangeColor(change: number): string {
  if (change > 0) return "text-emerald-600 dark:text-emerald-400"
  if (change < 0) return "text-rose-600 dark:text-rose-400"
  return "text-storm-400"
}

export function MetricCard({
  label,
  value,
  format = "number",
  decimals = 2,
  change,
  tooltip,
  className,
}: MetricCardProps) {
  const formatted = value === null || value === undefined
    ? "—"
    : formatters[format](value, decimals)

  const showChange = change !== undefined && change !== null

  return (
    <div
      className={cn(
        "metric-card",
        className
      )}
      data-tooltip={tooltip}
    >
      <div className="metric-label">{label}</div>
      <div className="flex items-baseline gap-2">
        <span
          className={cn(
            "metric-value",
            format === "score" && getScoreColor(value || 0),
            format !== "score" && "text-storm-900",
          )}
        >
          {formatted}
        </span>
        {showChange && (
          <span
            className={cn(
              "metric-change",
              getChangeColor(change)
            )}
          >
            {formatChange(change)}
          </span>
        )}
      </div>
      {format === "score" && value !== null && value !== undefined && (
        <div className="mt-2 h-1.5 rounded-full overflow-hidden bg-storm-100">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.max(0, Math.min(100, value))}%`,
              backgroundColor: getScoreColor(value).replace("text-", "bg-").replace("dark:text-", "dark:bg-"),
            }}
          />
        </div>
      )}
    </div>
  )
}