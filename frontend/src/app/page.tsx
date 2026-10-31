"use client"

import { useState, useCallback } from "react"
import { api } from "@/lib/api"
import { TextEditor } from "@/components/TextEditor"
import { AnalysisDisplay } from "@/components/AnalysisDisplay"
import { MetricCard } from "@/components/MetricCard"
import { cn } from "@/lib/utils"
import type { HumanizationStyle, HumanizationStrength, AnalyzeResponse, HumanizeResponse, CompareResponse, HealthResponse } from "@/lib/types"
import {
  BrainIcon,
  SparklesIcon,
  BarChartIcon,
  ZapIcon,
  FileTextIcon,
  LoaderIcon,
  CopyIcon,
  AlertCircleIcon,
  CheckCircleIcon,
  InfoIcon,
  SettingsIcon,
} from "@/components/icons"

const STYLES: { value: HumanizationStyle; label: string; Icon: React.ComponentType<{ size?: number; className?: string }> }[] = [
  { value: "natural", label: "Natural", Icon: SparklesIcon },
  { value: "academic", label: "Academic", Icon: FileTextIcon },
  { value: "professional", label: "Professional", Icon: ZapIcon },
  { value: "casual", label: "Casual", Icon: BrainIcon },
  { value: "technical", label: "Technical", Icon: SettingsIcon },
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
  const [mode, setMode] = useState<"analyze" | "humanize" | "compare">("analyze")
  const [loading, setLoading] = useState<"analyze" | "humanize" | "compare" | false>(false)
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
    setLoading("analyze")
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
    setLoading("humanize")
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
    if (!humanizedText.trim()) {
      setError("Please humanize the text first before comparing")
      return
    }
    setLoading("compare")
    setError(null)
    try {
      const res = await api.compare(originalText, style, strength)
      setCompareResult(res)
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

  // Transform analysis data to match frontend expected keys
  const transformAnalysis = (analysis: any) => {
    if (!analysis) return analysis
    return {
      ...analysis,
      lexical_metrics: {
        ...analysis.lexical_metrics,
        repeated_words: analysis.lexical_metrics?.most_repeated_words?.length || 0,
      },
    }
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
    <div className="min-h-screen bg-linen-100 dark:bg-storm-950">
      <header className="border-b border-storm-200 dark:border-storm-800 bg-white/80 dark:bg-storm-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-storm-100 dark:bg-storm-800 rounded-lg">
                <BrainIcon className="w-5 h-5 text-storm-700 dark:text-storm-200" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-storm-900 dark:text-storm-100 tracking-tight">AI Humanizer</h1>
                <p className="text-xs text-storm-500 dark:text-storm-400">NLP Naturalization & Writing-Pattern Analysis</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {health && (
                <div className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium",
                  health.model_loaded
                    ? "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                    : "bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300"
                )}>
                  <span className={cn("w-1.5 h-1.5 rounded-full", health.model_loaded ? "bg-emerald-500" : "bg-amber-500")} />
                  {health.model_loaded ? "Model Ready" : "Loading..."}
                  {health.gpu_available && health.gpu_memory_used_mb && (
                    <span className="text-storm-400 dark:text-storm-500 ml-2">
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
          <div className="mb-6 p-4 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-lg flex items-center justify-between animate-fade-in" role="alert">
            <div className="flex items-center gap-2">
              <AlertCircleIcon className="w-5 h-5 text-rose-600 dark:text-rose-400" />
              <span className="text-rose-700 dark:text-rose-300">{error}</span>
            </div>
            <button onClick={() => setError(null)} className="p-1 text-rose-500 hover:text-rose-700 dark:hover:text-rose-300 rounded-md transition-colors">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-6">
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Original Text</h2>
              </div>
              <div className="card-body p-0">
                <TextEditor
                  label="Original Text"
                  value={originalText}
                  onChange={setOriginalText}
                  placeholder="Paste your text here to analyze or humanize..."
                  showStats={true}
                />
              </div>

              <div className="card-header bg-storm-50 dark:bg-storm-900/30">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-2">
                    <label className="text-sm font-medium text-storm-700 dark:text-storm-200">Style:</label>
                    <select
                      value={style}
                      onChange={(e) => setStyle(e.target.value as HumanizationStyle)}
                      className="input select min-w-[140px]"
                    >
                      {STYLES.map(s => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-2">
                    <label className="text-sm font-medium text-storm-700 dark:text-storm-200">Strength:</label>
                    <select
                      value={strength}
                      onChange={(e) => setStrength(e.target.value as HumanizationStrength)}
                      className="input select min-w-[140px]"
                    >
                      {STRENGTHS.map(s => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="card-header bg-storm-50 dark:bg-storm-900/30 pt-0">
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={handleAnalyze}
                    disabled={loading === "analyze" || !originalText.trim()}
                    className={cn(
                      "btn btn-primary",
                      loading === "analyze" || !originalText.trim()
                        ? "opacity-50 cursor-not-allowed"
                        : ""
                    )}
                  >
                    {loading === "analyze" ? (
                      <> <LoaderIcon size={16} className="animate-spin" /> Analyzing... </> ) : (
                      <> <BrainIcon size={16} /> Analyze </> )}
                  </button>

                  <button
                    onClick={handleHumanize}
                    disabled={loading === "humanize" || !originalText.trim()}
                    className={cn(
                      "btn btn-secondary",
                      loading === "humanize" || !originalText.trim()
                        ? "opacity-50 cursor-not-allowed"
                        : ""
                    )}
                  >
                    {loading === "humanize" ? (
                      <> <LoaderIcon size={16} className="animate-spin" /> Humanizing... </> ) : (
                      <> <SparklesIcon size={16} /> Humanize </> )}
                  </button>

                  <button
                    onClick={handleCompare}
                    disabled={loading === "compare" || !originalText.trim() || !humanizedText.trim()}
                    className={cn(
                      "btn btn-accent",
                      loading === "compare" || !originalText.trim() || !humanizedText.trim()
                        ? "opacity-50 cursor-not-allowed"
                        : ""
                    )}
                    title={!humanizedText.trim() ? "Humanize text first before comparing" : undefined}
                  >
                    {loading === "compare" ? (
                      <> <LoaderIcon size={16} className="animate-spin" /> Comparing... </> ) : (
                      <> <BarChartIcon size={16} /> Compare </> )}
                  </button>

                  <button
                    onClick={handleClear}
                    className="btn btn-ghost"
                  >
                    Clear
                  </button>
                </div>
              </div>

              {humanizedText && (
                <div className="card-header bg-emerald-50 dark:bg-emerald-900/20 border-t border-emerald-200 dark:border-emerald-800 pt-0">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-emerald-700 dark:text-emerald-300">Humanized Output</h3>
                    <button
                      onClick={() => navigator.clipboard.writeText(humanizedText)}
                      className="p-1.5 text-emerald-600 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors rounded-md"
                      aria-label="Copy to clipboard"
                    >
                      <CopyIcon size={16} />
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
                analysis={transformAnalysis(analyzeResult.analysis)}
                naturalness={analyzeResult.naturalness_score || undefined}
                warnings={analyzeResult.warnings}
                title="Analysis Results"
              />
            )}

            {mode === "humanize" && humanizeResult && (
              <div className="space-y-4 animate-fade-in">
                <div className="card">
                  <div className="card-header bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800">
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                      <h3 className="text-emerald-700 dark:text-emerald-300 font-medium">Humanization Complete</h3>
                    </div>
                  </div>
                  <div className="card-body">
                    <p className="text-sm text-storm-600 dark:text-storm-400 mb-3">
                      Humanization complete. The text has been rewritten with the selected style and strength.
                      Click <strong className="text-accent-600 dark:text-accent-400">"Compare"</strong> to see detailed before/after metrics.
                    </p>
                    {humanizeResult.semantic_similarity !== null && (
                      <div className="flex items-center gap-3 p-3 bg-storm-50 dark:bg-storm-900/30 rounded-lg">
                        <InfoIcon className="w-5 h-5 text-storm-500" />
                        <div>
                          <span className="text-sm font-medium text-storm-700 dark:text-storm-200">Semantic Similarity: </span>
                          <span className="font-mono text-lg font-semibold text-accent-600 dark:text-accent-400">
                            {(humanizeResult.semantic_similarity * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )}
                    {humanizeResult.content_preservation_warnings.length > 0 && (
                      <div className="space-y-2 mt-3">
                        {humanizeResult.content_preservation_warnings.map((w, i) => (
                          <div key={i} className="p-3 text-sm bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-amber-700 dark:text-amber-300 flex items-start gap-2">
                            <AlertCircleIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
                            <span>{w.message}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {mode === "compare" && compareResult && (
              <AnalysisDisplay
                analysis={transformAnalysis(compareResult.humanized_analysis)}
                naturalness={compareResult.naturalness_score_after}
                warnings={compareResult.content_preservation_warnings}
                title="Comparison: Original vs Humanized"
                comparisonData={comparisonData}
              />
            )}

            {!analyzeResult && !humanizeResult && !compareResult && (
              <div className="card text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-storm-100 dark:bg-storm-800 flex items-center justify-center">
                  <BrainIcon className="w-8 h-8 text-storm-500 dark:text-storm-400" />
                </div>
                <h3 className="text-lg font-semibold text-storm-900 dark:text-storm-100 mb-2">Ready to Analyze</h3>
                <p className="text-storm-500 dark:text-storm-400 max-w-md mx-auto mb-6">
                  Paste text in the editor and click <strong className="text-storm-700 dark:text-storm-300">Analyze</strong>, <strong className="text-storm-700 dark:text-storm-300">Humanize</strong>, or <strong className="text-storm-700 dark:text-storm-300">Compare</strong> to see detailed linguistic metrics and naturalness scores.
                </p>
                <div className="grid grid-cols-3 gap-4 max-w-md mx-auto">
                  <div className="p-4 bg-storm-50 dark:bg-storm-900/30 rounded-lg">
                    <div className="text-2xl font-bold text-storm-700 dark:text-storm-300">30+</div>
                    <div className="text-xs text-storm-500 dark:text-storm-400">Linguistic Metrics</div>
                  </div>
                  <div className="p-4 bg-storm-50 dark:bg-storm-900/30 rounded-lg">
                    <div className="text-2xl font-bold text-accent-600 dark:text-accent-400">5</div>
                    <div className="text-xs text-storm-500 dark:text-storm-400">Style Options</div>
                  </div>
                  <div className="p-4 bg-storm-50 dark:bg-storm-900/30 rounded-lg">
                    <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">Local</div>
                    <div className="text-xs text-storm-500 dark:text-storm-400">LLM Processing</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-storm-200 dark:border-storm-800 bg-white/80 dark:bg-storm-950/80 backdrop-blur-sm mt-12">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <p className="text-xs text-storm-500 dark:text-storm-400 text-center">
            AI Humanizer / NLP Naturalization System — Research Tool ·
            <span className="mx-2">·</span>
            Not an AI Detector ·
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