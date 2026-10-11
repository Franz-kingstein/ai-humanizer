"use client"

import { useState, useCallback } from "react"
import { api } from "@/lib/api"
import { TextEditor } from "@/components/TextEditor"
import { AnalysisDisplay } from "@/components/AnalysisDisplay"
import { MetricCard } from "@/components/MetricCard"
import { cn } from "@/lib/utils"
import type { HumanizationStyle, HumanizationStrength, AnalyzeResponse, HumanizeResponse, CompareResponse, HealthResponse } from "@/lib/types"
import { Loader2, Sparkles, Brain, AlertTriangle, CheckCircle, XCircle, Zap, FileText, BarChart2 } from "lucide-react"

const STYLES: { value: HumanizationStyle; label: string; icon: React.ReactNode }[] = [
  { value: "natural", label: "Natural", icon: <Sparkles className="w-4 h-4" /> },
  { value: "academic", label: "Academic", icon: <FileText className="w-4 h-4" /> },
  { value: "professional", label: "Professional", icon: <Zap className="w-4 h-4" /> },
  { value: "casual", label: "Casual", icon: <Brain className="w-4 h-4" /> },
  { value: "technical", label: "Technical", icon: <BarChart2 className="w-4 h-4" /> },
]

const STRENGTHS: { value: HumanizationStrength; label: string; description: string }[] = [
  { value: "low", label: "Low", description: "Light polishing" },
  { value: "medium", label: "Medium", description: "Balanced restructuring" },
  { value: "high", label: "High", description: "Maximum naturalness" },
]

export default function HomePage() {
  const [originalText, setOriginalText] = useState("")
  const [humanizedText, setHumanizedText] = useState("")
  const [style, setStyle] = useState<HumanizationStyle>("natural")
  const [strength, setStrength] = useState<HumanizationStrength>("medium")
  const [mode, setMode] = useState<"analyze" | "humanize" | "compare">("compare")
  const [loading, setLoading] = useState(false)
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeResponse | null>(null)
  const [humanizeResult, setHumanizeResult] = useState<HumanizeResponse | null>(null)
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const checkHealth = useCallback(async () => {
    try {
      const res = await api.health()
      setHealth(res)
    } catch {
      setHealth({ status: "unhealthy", version: "unknown", model_loaded: false, device: "unknown", gpu_available: false, gpu_memory_used_mb: null, gpu_memory_total_mb: null })
    }
  }, [])

  const handleAnalyze = async () => {
    if (!originalText.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.analyze(originalText)
      setAnalyzeResult(res)
      setMode("analyze")
    } catch (e: any) {
      setError(e.response?.data?.detail || "Analysis failed")
    } finally {
      setLoading(false)
    }
  }

  const handleHumanize = async () => {
    if (!originalText.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.humanize(originalText, style, strength)
      setHumanizeResult(res)
      setHumanizedText(res.humanized_text)
      setMode("humanize")
    } catch (e: any) {
      setError(e.response?.data?.detail || "Humanization failed")
    } finally {
      setLoading(false)
    }
  }

  const handleCompare = async () => {
    if (!originalText.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.compare(originalText, style, strength)
      setCompareResult(res)
      setHumanizedText(res.humanized_text)
      setMode("compare")
    } catch (e: any) {
      setError(e.response?.data?.detail || "Comparison failed")
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setOriginalText("")
    setHumanizedText("")
    setAnalyzeResult(null)
    setHumanizeResult(null)
    setCompareResult(null)
    setError(null)
  }

  const comparisonData = compareResult ? {
    "Word Count": { before: compareResult.original_analysis.basic_stats.word_count, after: compareResult.humanized_analysis.basic_stats.word_count },
    "Sentence Count": { before: compareResult.original_analysis.basic_stats.sentence_count, after: compareResult.humanized_analysis.basic_stats.sentence_count },
    "Avg Sentence Length": { before: compareResult.original_analysis.basic_stats.avg_sentence_length, after: compareResult.humanized_analysis.basic_stats.avg_sentence_length },
    "Type-Token Ratio": { before: compareResult.original_analysis.lexical_metrics.type_token_ratio || 0, after: compareResult.humanized_analysis.lexical_metrics.type_token_ratio || 0 },
    "Flesch Reading Ease": { before: compareResult.original_analysis.readability.flesch_reading_ease || 0, after: compareResult.humanized_analysis.readability.flesch_reading_ease || 0 },
    "Bigram Repetition": { before: compareResult.original_analysis.ngram_repetition.bigram_repetition_ratio, after: compareResult.humanized_analysis.ngram_repetition.bigram_repetition_ratio },
    "Template Density": { before: compareResult.original_analysis.template_phrases.template_phrase_density, after: compareResult.humanized_analysis.template_phrases.template_phrase_density },
    "Passive Ratio": { before: compareResult.original_analysis.passive_voice.passive_ratio, after: compareResult.humanized_analysis.passive_voice.passive_ratio },
    "Naturalness": { before: compareResult.naturalness_score_before.score, after: compareResult.naturalness_score_after.score },
  } : undefined

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Sparkles className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">AI Humanizer</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">NLP Naturalization & Writing-Pattern Analysis</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {health && (
                <div className={cn(
                  "flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium",
                  health.model_loaded
                    ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                    : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300"
                )}>
                  <span className={cn("w-2 h-2 rounded-full", health.model_loaded ? "bg-green-500" : "bg-yellow-500")} />
                  {health.model_loaded ? "Model Ready" : "Loading..."}
                  {health.gpu_available && health.gpu_memory_used_mb && (
                    <span className="text-gray-500 dark:text-gray-400 ml-2">
                      GPU: {health.gpu_memory_used_mb}MB / {health.gpu_memory_total_mb}MB
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
              <span className="text-red-700 dark:text-red-300">{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">×</button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-6">
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Original Text</h2>
              <TextEditor
                label="Original Text"
                value={originalText}
                onChange={setOriginalText}
                placeholder="Paste your text here to analyze or humanize..."
                showStats={true}
              />

              <div className="mt-4 flex flex-wrap gap-3">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Style:</label>
                  <select
                    value={style}
                    onChange={(e) => setStyle(e.target.value as HumanizationStyle)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {STYLES.map(s => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Strength:</label>
                  <select
                    value={strength}
                    onChange={(e) => setStrength(e.target.value as HumanizationStrength)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {STRENGTHS.map(s => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  onClick={handleAnalyze}
                  disabled={loading || !originalText.trim()}
                  className={cn(
                    "px-6 py-2.5 rounded-lg font-medium text-sm transition-all",
                    "focus:outline-none focus:ring-2 focus:ring-offset-2",
                    loading || !originalText.trim()
                      ? "bg-gray-300 dark:bg-gray-600 text-gray-500 cursor-not-allowed"
                      : "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500"
                  )}
                >
                  {loading ? (
                    <> <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing... </> ) : (
                    <> <Brain className="w-4 h-4 mr-2" /> Analyze </> )}
                </button>

                <button
                  onClick={handleHumanize}
                  disabled={loading || !originalText.trim()}
                  className={cn(
                    "px-6 py-2.5 rounded-lg font-medium text-sm transition-all",
                    "focus:outline-none focus:ring-2 focus:ring-offset-2",
                    loading || !originalText.trim()
                      ? "bg-gray-300 dark:bg-gray-600 text-gray-500 cursor-not-allowed"
                      : "bg-purple-600 text-white hover:bg-purple-700 focus:ring-purple-500"
                  )}
                >
                  {loading ? (
                    <> <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing... </> ) : (
                    <> <Sparkles className="w-4 h-4 mr-2" /> Humanize </> )}
                </button>

                <button
                  onClick={handleCompare}
                  disabled={loading || !originalText.trim()}
                  className={cn(
                    "px-6 py-2.5 rounded-lg font-medium text-sm transition-all",
                    "focus:outline-none focus:ring-2 focus:ring-offset-2",
                    loading || !originalText.trim()
                      ? "bg-gray-300 dark:bg-gray-600 text-gray-500 cursor-not-allowed"
                      : "bg-green-600 text-white hover:bg-green-700 focus:ring-green-500"
                  )}
                >
                  {loading ? (
                    <> <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing... </> ) : (
                    <> <BarChart2 className="w-4 h-4 mr-2" /> Compare </> )}
                </button>

                <button
                  onClick={handleClear}
                  className="px-4 py-2.5 rounded-lg font-medium text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                >
                  Clear
                </button>
              </div>

              {humanizedText && (
                <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-green-700 dark:text-green-300">Humanized Output</h3>
                    <button
                      onClick={() => navigator.clipboard.writeText(humanizedText)}
                      className="text-xs text-green-600 dark:text-green-400 hover:underline"
                    >
                      Copy
                    </button>
                  </div>
                  <TextEditor
                    label="Humanized Output"
                    value={humanizedText}
                    onChange={setHumanizedText}
                    readOnly
                    showStats={true}
                  />
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            {mode === "analyze" && analyzeResult && (
              <AnalysisDisplay
                analysis={analyzeResult.analysis}
                naturalness={analyzeResult.naturalness_score || undefined}
                warnings={analyzeResult.warnings}
                title="Analysis Results"
              />
            )}

            {mode === "humanize" && humanizeResult && (
              <AnalysisDisplay
                analysis={{
                  ...humanizeResult,
                  analysis: humanizeResult as any,
                } as any}
                warnings={humanizeResult.content_preservation_warnings}
                title="Humanization Result"
              />
            )}

            {mode === "compare" && compareResult && (
              <AnalysisDisplay
                analysis={compareResult.humanized_analysis}
                naturalness={compareResult.naturalness_score_after}
                warnings={compareResult.content_preservation_warnings}
                title="Comparison: Humanized Text"
                comparisonData={comparisonData}
              />
            )}

            {!analyzeResult && !humanizeResult && !compareResult && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
                <Brain className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">Ready to Analyze</h3>
                <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                  Paste text in the editor and click <strong>Analyze</strong>, <strong>Humanize</strong>, or <strong>Compare</strong> to see detailed linguistic metrics and naturalness scores.
                </p>
                <div className="mt-6 grid grid-cols-3 gap-4 text-center">
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">30+</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Linguistic Metrics</div>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">5</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Style Options</div>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">Local</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">LLM Processing</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm mt-12">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            AI Humanizer / NLP Naturalization System — Research Tool · Not an AI Detector ·
            <span className="mx-2">·</span>
            Naturalness Score is a heuristic metric ·
            <span className="mx-2">·</span>
            Privacy: Text not stored by default
          </p>
        </div>
      </footer>
    </div>
  )
}