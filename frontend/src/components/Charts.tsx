"use client"

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  RadialBarChart,
  RadialBar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
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
      range: `${range}-${Number(range) + binSize - 1}`,
      count,
    }))

  return (
    <div className={cn("h-64", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: "#6b7280" }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="range"
            width={80}
            tick={{ fontSize: 11, fill: "#6b7280" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "none",
              borderRadius: "8px",
              color: "#f9fafb",
            }}
          />
          <Legend />
          <Bar
            dataKey="count"
            fill="#3b82f6"
            radius={[0, 4, 4, 0]}
            maxBarSize={30}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill="hsl(217, 91%, 60%)" />
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
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="metric"
            tick={{ fontSize: 11, fill: "#6b7280" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis tick={{ fontSize: 11, fill: "#6b7280" }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "none",
              borderRadius: "8px",
              color: "#f9fafb",
            }}
          />
          <Legend />
          <Bar dataKey="before" fill="#9ca3af" radius={[4, 4, 0, 0]} name="Before" maxBarSize={25} />
          <Bar dataKey="after" fill="#3b82f6" radius={[4, 4, 0, 0]} name="After" maxBarSize={25} />
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
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#6b7280" }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="metric"
            width={140}
            tick={{ fontSize: 11, fill: "#6b7280" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "none",
              borderRadius: "8px",
              color: "#f9fafb",
            }}
          />
          <Legend />
          <Bar
            dataKey="value"
            fill="#3b82f6"
            radius={[0, 4, 4, 0]}
            maxBarSize={25}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill="hsl(217, 91%, 60%)" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}