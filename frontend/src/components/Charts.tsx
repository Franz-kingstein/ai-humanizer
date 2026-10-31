"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts"
import { cn } from "@/lib/utils"

interface SentenceLengthChartProps {
  lengths: number[]
  className?: string
}

export function SentenceLengthChart({ lengths, className }: SentenceLengthChartProps) {
  if (!lengths.length) return null

  const maxLen = Math.max(...lengths)
  const binSize = Math.max(1, Math.ceil(maxLen / 15))
  const bins: Record<number, number> = {}

  lengths.forEach(len => {
    const bin = Math.floor(len / binSize) * binSize
    bins[bin] = (bins[bin] || 0) + 1
  })

  const data = Object.entries(bins)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([range, count]) => ({
      range: `${range}–${Number(range) + binSize - 1}`,
      count,
    }))

  return (
    <div className={cn("h-64", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-storm-100)" vertical={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: "var(--color-storm-400)" }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="range"
            width={80}
            tick={{ fontSize: 11, fill: "var(--color-storm-400)" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--color-storm-900)",
              border: "none",
              borderRadius: "8px",
              color: "white",
            }}
            formatter={(value: any) => [Number(value) ?? 0, "sentences"]}
          />
          <Legend />
          <Bar
            dataKey="count"
            fill="var(--color-accent-500)"
            radius={[0, 4, 4, 0]}
            maxBarSize={30}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill="var(--color-accent-500)" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

interface ComparisonChartProps {
  before: Record<string, number>
  after: Record<string, number>
  labels: Record<string, string>
  className?: string
}

export function ComparisonChart({ before, after, labels, className }: ComparisonChartProps) {
  const metrics = Object.keys(labels)
  const data = metrics.map(key => ({
    metric: labels[key],
    before: before[key] ?? 0,
    after: after[key] ?? 0,
  }))

  return (
    <div className={cn("h-72", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-storm-100)" />
          <XAxis
            dataKey="metric"
            tick={{ fontSize: 11, fill: "var(--color-storm-400)" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis tick={{ fontSize: 11, fill: "var(--color-storm-400)" }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--color-storm-900)",
              border: "none",
              borderRadius: "8px",
              color: "white",
            }}
          />
          <Legend />
          <Bar dataKey="before" fill="var(--color-storm-300)" radius={[4, 4, 0, 0]} name="Before" maxBarSize={25} />
          <Bar dataKey="after" fill="var(--color-accent-500)" radius={[4, 4, 0, 0]} name="After" maxBarSize={25} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

interface RadarChartProps {
  data: Array<{ metric: string; value: number }>
  className?: string
}

export function RadarChart({ data, className }: RadarChartProps) {
  if (!data.length) return null

  return (
    <div className={cn("h-72", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-storm-100)" vertical={false} />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "var(--color-storm-400)" }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="metric"
            width={140}
            tick={{ fontSize: 11, fill: "var(--color-storm-400)" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--color-storm-900)",
              border: "none",
              borderRadius: "8px",
              color: "white",
            }}
            formatter={(value: any) => [Number(value) ?? 0, "score"]}
          />
          <Legend />
          <Bar
            dataKey="value"
            fill="var(--color-accent-500)"
            radius={[0, 4, 4, 0]}
            maxBarSize={25}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill="var(--color-accent-500)" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}