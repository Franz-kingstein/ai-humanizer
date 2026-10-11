"use client"

import { cn, formatNumber, formatPercent, formatRatio, getScoreColor, getScoreBg, getChangeColor } from "@/lib/utils"

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
  number: (v: number, d: number) => formatNumber(v, d),
  percent: (v: number, d: number) => formatPercent(v, d),
  ratio: (v: number, d: number) => formatRatio(v, d),
  score: (v: number) => v.toFixed(1),
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
        "p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700",
        "transition-all duration-200 hover:border-gray-300 dark:hover:border-gray-600",
        className
      )}
      title={tooltip}
    >
      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className="flex items-baseline gap-2">
        <span
          className={cn(
            "text-2xl font-mono font-semibold",
            format === "score" && getScoreColor(value || 0),
            format !== "score" && "text-gray-900 dark:text-gray-100"
          )}
        >
          {formatted}
        </span>
        {showChange && (
          <span
            className={cn(
              "text-sm font-medium",
              getChangeColor(change)
            )}
          >
            {formatChange(change)}
          </span>
        )}
      </div>
      {format === "score" && value !== null && value !== undefined && (
        <div className="mt-2 h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
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

function formatChange(change: number): string {
  const sign = change > 0 ? "+" : ""
  return `${sign}${change.toFixed(2)}`
}