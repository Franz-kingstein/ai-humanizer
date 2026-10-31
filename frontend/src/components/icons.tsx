"use client"

import { SVGProps } from "react"

interface IconProps extends SVGProps<SVGSVGElement> {
  size?: number | string
}

const iconSize = (size?: number | string) => {
  if (typeof size === "number") return `${size}px`
  return size || "1em"
}

export function BrainIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <path d="M12 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z" />
      <path d="M12 5v6" />
      <path d="M12 17v6" />
      <path d="M5 9c0-2 2-3 4-3s4 1 4 3" />
      <path d="M15 9c0-2 2-3 4-3s4 1 4 3" />
      <path d="M5 15c0 2 2 3 4 3s4-1 4-3" />
      <path d="M15 15c0 2 2 3 4 3s4-1 4-3" />
    </svg>
  )
}

export function SparklesIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <path d="M12 3v4" />
      <path d="M12 17v4" />
      <path d="M3 12h4" />
      <path d="M17 12h4" />
      <path d="M5 5l4 4" />
      <path d="M15 5l-4 4" />
      <path d="M5 19l4-4" />
      <path d="M15 19l-4-4" />
    </svg>
  )
}

export function BarChartIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <path d="M3 3v18h18" />
      <rect x="7" y="13" width="3" height="5" rx="0.5" />
      <rect x="12" y="8" width="3" height="10" rx="0.5" />
      <rect x="17" y="16" width="3" height="2" rx="0.5" />
    </svg>
  )
}

export function ZapIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  )
}

export function FileTextIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" x2="8" y1="13" y2="13" />
      <line x1="16" x2="8" y1="17" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  )
}

export function LoaderIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      className={`${className} animate-spin`}
      {...props}
    >
      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" />
    </svg>
  )
}

export function CopyIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  )
}

export function ChevronRightIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  )
}

export function XIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  )
}

export function AlertCircleIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" x2="12" y1="8" y2="12" />
      <line x1="12" x2="12.01" y1="16" y2="16" />
    </svg>
  )
}

export function CheckCircleIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}

export function InfoIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" x2="12" y1="16" y2="16" />
      <line x1="12" x2="12.01" y1="8" y2="12" />
    </svg>
  )
}

export function MetricChangeIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <polyline points="23 4 13 16 9 12 9 12 5 16 1 8" />
    </svg>
  )
}

export function SettingsIcon({ size, className, ...props }: IconProps) {
  return (
    <svg
      width={iconSize(size)}
      height={iconSize(size)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </svg>
  )
}