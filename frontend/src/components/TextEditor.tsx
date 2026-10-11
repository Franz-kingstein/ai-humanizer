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
}

export function TextEditor({
  label,
  value,
  onChange,
  placeholder,
  readOnly = false,
  showStats = true,
  className,
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
    <div className={cn("flex flex-col", className)}>
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label}
      </label>
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          placeholder={placeholder}
          readOnly={readOnly}
          rows={8}
          className={cn(
            "w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg",
            "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100",
            "placeholder-gray-400 dark:placeholder-gray-500",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
            "resize-y min-h-[200px] font-mono text-sm leading-relaxed",
            readOnly && "bg-gray-50 dark:bg-gray-900/50 cursor-not-allowed",
            "transition-all duration-200"
          )}
          style={{ height: `${height}px` }}
        />
        {showStats && (
          <div className="absolute bottom-2 right-2 flex gap-4 text-xs text-gray-500 dark:text-gray-400 bg-white/80 dark:bg-gray-800/80 px-2 py-1 rounded">
            <span>{wordCount} words</span>
            <span>{charCount} chars</span>
            <span>{sentenceCount} sentences</span>
          </div>
        )}
      </div>
    </div>
  )
}