import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(num: number | null | undefined, decimals = 2): string {
  if (num === null || num === undefined) return "—"
  return num.toFixed(decimals)
}

export function formatPercent(num: number | null | undefined, decimals = 1): string {
  if (num === null || num === undefined) return "—"
  return `${num.toFixed(decimals)}%`
}

export function formatRatio(num: number | null | undefined, decimals = 4): string {
  if (num === null || num === undefined) return "—"
  return num.toFixed(decimals)
}

export function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-600 dark:text-green-400"
  if (score >= 60) return "text-yellow-600 dark:text-yellow-400"
  if (score >= 40) return "text-orange-600 dark:text-orange-400"
  return "text-red-600 dark:text-red-400"
}

export function getScoreBg(score: number): string {
  if (score >= 80) return "bg-green-100 dark:bg-green-900/30"
  if (score >= 60) return "bg-yellow-100 dark:bg-yellow-900/30"
  if (score >= 40) return "bg-orange-100 dark:bg-orange-900/30"
  return "bg-red-100 dark:bg-red-900/30"
}

export function getChangeColor(change: number): string {
  if (change > 0) return "text-green-600 dark:text-green-400"
  if (change < 0) return "text-red-600 dark:text-red-400"
  return "text-gray-500 dark:text-gray-400"
}

export function formatChange(change: number): string {
  const sign = change > 0 ? "+" : ""
  return `${sign}${change.toFixed(2)}`
}

export function getReadabilityLabel(score: number | null): string {
  if (score === null) return "Unknown"
  if (score >= 90) return "Very Easy"
  if (score >= 80) return "Easy"
  if (score >= 70) return "Fairly Easy"
  if (score >= 60) return "Standard"
  if (score >= 50) return "Fairly Difficult"
  if (score >= 30) return "Difficult"
  return "Very Difficult"
}