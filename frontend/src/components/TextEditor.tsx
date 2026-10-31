"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"

interface TextEditorProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  readOnly?: boolean
  showStats?: boolean
  className?: string
  onCopy?: () => void
}

const CopyIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
)

export function TextEditor({
  label,
  value,
  onChange,
  placeholder,
  readOnly = false,
  showStats = true,
  className,
  onCopy,
}: TextEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [height, setHeight] = useState(200)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      const newHeight = Math.max(textareaRef.current.scrollHeight, 200)
      setHeight(newHeight)
    }
  }, [value])

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value)
  }

  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0
  const charCount = value.length
  const sentenceCount = value.split(/[.!?]+/).filter(s => s.trim().length > 0).length

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-storm-700 dark:text-storm-200">
          {label}
        </label>
        {onCopy && (
          <button
            onClick={onCopy}
            className="p-1.5 text-storm-400 hover:text-storm-600 dark:hover:text-storm-300 transition-colors rounded-md"
            aria-label="Copy to clipboard"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
          </button>
        )}
      </div>
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          placeholder={placeholder}
          readOnly={readOnly}
          rows={8}
          className={`input textarea transition-all duration-200 ${readOnly ? "bg-storm-50 dark:bg-storm-900/30 cursor-not-allowed" : ""}`}
          style={{ height: `${height}px` }}
        />
        {showStats && (
          <div className="absolute bottom-2 right-2 flex gap-3 text-xs text-storm-400 dark:text-storm-500 bg-white/90 dark:bg-storm-900/90 px-2 py-1 rounded border border-storm-100 dark:border-storm-800">
            <span>{wordCount.toLocaleString()} words</span>
            <span>{charCount.toLocaleString()} chars</span>
            <span>{sentenceCount.toLocaleString()} sent.</span>
          </div>
        )}
      </div>
    </div>
  )
}