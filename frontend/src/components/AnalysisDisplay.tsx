"use client"

import { AnalysisResult, NaturalnessScore, Warning } from "@/lib/types"
import { MetricCard } from "./MetricCard"
import { cn, formatNumber, formatPercent, formatRatio, getReadabilityLabel } from "@/lib/utils"
import { SentenceLengthChart, ComparisonChart, RadarChart } from "./Charts"
import { AlertCircleIcon, InfoIcon, CheckCircleIcon, ChevronRightIcon } from "./icons"

interface AnalysisDisplayProps {
  analysis: AnalysisResult
  naturalness?: NaturalnessScore
  warnings?: Warning[]
  title?: string
  comparisonData?: Record<string, { before: number; after: number }>
}

interface MetricDef {
  label: string
  key: string
  format: "number" | "percent" | "ratio"
  decimals?: number
  tooltipKey?: string
}

const METRIC_GROUPS: { title: string; key: string; metrics: MetricDef[] }[] = [
  {
    title: "Basic Statistics",
    key: "basic",
    metrics: [
      { label: "Words", key: "word_count", format: "number" },
      { label: "Unique Words", key: "unique_word_count", format: "number" },
      { label: "Sentences", key: "sentence_count", format: "number" },
      { label: "Paragraphs", key: "paragraph_count", format: "number" },
      { label: "Avg Word Length", key: "avg_word_length", format: "number", decimals: 1 },
      { label: "Avg Sentence Length", key: "avg_sentence_length", format: "number", decimals: 1 },
    ],
  },
  {
    title: "Sentence Structure",
    key: "sentence",
    metrics: [
      { label: "Min Length", key: "min_length", format: "number" },
      { label: "Max Length", key: "max_length", format: "number" },
      { label: "Mean Length", key: "mean_length", format: "number", decimals: 1 },
      { label: "Median Length", key: "median_length", format: "number", decimals: 1 },
      { label: "Std Deviation", key: "std_dev", format: "number", decimals: 1 },
      { label: "Coeff. of Variation", key: "coefficient_of_variation", format: "ratio" },
    ],
  },
  {
    title: "Lexical Diversity",
    key: "lexical",
    metrics: [
      { label: "Type-Token Ratio", key: "type_token_ratio", format: "ratio" },
      { label: "Root TTR (Guiraud)", key: "root_ttr", format: "ratio" },
      { label: "Herdan's C", key: "herdan_c", format: "ratio" },
      { label: "Lexical Density", key: "lexical_density", format: "percent", decimals: 1 },
      { label: "Hapax Legomena Ratio", key: "hapax_legomena_ratio", format: "ratio" },
      { label: "Repeated Words", key: "repeated_words", format: "number" },
    ],
  },
  {
    title: "Readability",
    key: "readability",
    metrics: [
      { label: "Flesch Reading Ease", key: "flesch_reading_ease", format: "number", decimals: 1, tooltipKey: "readability_tooltip" },
      { label: "Flesch-Kincaid Grade", key: "flesch_kincaid_grade", format: "number", decimals: 1 },
      { label: "Gunning Fog", key: "gunning_fog", format: "number", decimals: 1 },
      { label: "SMOG Index", key: "smog_index", format: "number", decimals: 1 },
      { label: "Automated Readability", key: "automated_readability_index", format: "number", decimals: 1 },
      { label: "Coleman-Liau", key: "coleman_liau_index", format: "number", decimals: 1 },
    ],
  },
  {
    title: "Repetition & Templates",
    key: "repetition",
    metrics: [
      { label: "Bigram Repetition", key: "bigram_repetition_ratio", format: "ratio" },
      { label: "Trigram Repetition", key: "trigram_repetition_ratio", format: "ratio" },
      { label: "Unique Bigrams", key: "unique_bigrams", format: "number" },
      { label: "Unique Trigrams", key: "unique_trigrams", format: "number" },
      { label: "Template Density (per 1k)", key: "template_phrase_density", format: "number", decimals: 1 },
      { label: "Templates Used", key: "unique_templates_used", format: "number" },
    ],
  },
  {
    title: "Passive Voice",
    key: "passive",
    metrics: [
      { label: "Passive Sentences", key: "passive_sentences", format: "number" },
      { label: "Total Sentences", key: "total_sentences", format: "number" },
      { label: "Passive Ratio", key: "passive_ratio", format: "percent", decimals: 1 },
    ],
  },
]

function getNestedValue(obj: any, path: string): any {
  return path.split(".").reduce((o, k) => (o || {})[k], obj)
}

export function AnalysisDisplay({
  analysis,
  naturalness,
  warnings = [],
  title = "Analysis Results",
  comparisonData,
}: AnalysisDisplayProps) {
  const basic_stats = analysis.basic_stats
  const sentence_stats = analysis.sentence_stats
  const lexical_metrics = analysis.lexical_metrics
  const readability = analysis.readability
  const ngram_repetition = analysis.ngram_repetition
  const template_phrases = analysis.template_phrases
  const passive_voice = analysis.passive_voice

  // Flatten all nested data for easy lookup by flat keys
  const dataMap = {
    // Basic stats
    word_count: basic_stats?.word_count,
    unique_word_count: basic_stats?.unique_word_count,
    sentence_count: basic_stats?.sentence_count,
    paragraph_count: basic_stats?.paragraph_count,
    avg_word_length: basic_stats?.avg_word_length,
    avg_sentence_length: basic_stats?.avg_sentence_length,
    
    // Sentence stats
    min_length: sentence_stats?.min_length,
    max_length: sentence_stats?.max_length,
    mean_length: sentence_stats?.mean_length,
    median_length: sentence_stats?.median_length,
    std_dev: sentence_stats?.std_dev,
    coefficient_of_variation: sentence_stats?.coefficient_of_variation,
    
    // Lexical metrics
    type_token_ratio: lexical_metrics?.type_token_ratio,
    root_ttr: lexical_metrics?.root_ttr,
    herdan_c: lexical_metrics?.herdan_c,
    lexical_density: lexical_metrics?.lexical_density,
    hapax_legomena_ratio: lexical_metrics?.hapax_legomena_ratio,
    repeated_words: lexical_metrics?.most_repeated_words?.length || 0,
    
    // Readability
    flesch_reading_ease: readability?.flesch_reading_ease,
    flesch_kincaid_grade: readability?.flesch_kincaid_grade,
    gunning_fog: readability?.gunning_fog,
    smog_index: readability?.smog_index,
    automated_readability_index: readability?.automated_readability_index,
    coleman_liau_index: readability?.coleman_liau_index,
    
    // Repetition & Templates
    bigram_repetition_ratio: ngram_repetition?.bigram_repetition_ratio,
    trigram_repetition_ratio: ngram_repetition?.trigram_repetition_ratio,
    unique_bigrams: ngram_repetition?.unique_bigrams,
    unique_trigrams: ngram_repetition?.unique_trigrams,
    template_phrase_density: template_phrases?.template_phrase_density,
    unique_templates_used: template_phrases?.unique_templates_used,
    
    // Passive Voice
    passive_sentences: passive_voice?.passive_sentences,
    total_sentences: passive_voice?.total_sentences,
    passive_ratio: passive_voice?.passive_ratio,
    
    // Computed
    readability_tooltip: getReadabilityLabel(readability?.flesch_reading_ease),
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-semibold text-storm-900 dark:text-storm-100">{title}</h2>
        {naturalness && (
          <MetricCard
            label="Naturalness Score"
            value={naturalness.score}
            format="score"
            className="min-w-[180px]"
          />
        )}
      </div>

      {warnings.length > 0 && (
        <div className="space-y-2" role="alert">
          {warnings.map((w, i) => (
            <div
              key={i}
              className={cn(
                "p-3 rounded-lg text-sm border-l-4 flex items-start gap-3",
                w.severity === "error" && "bg-rose-50 dark:bg-rose-900/20 border-rose-500 text-rose-700 dark:text-rose-300",
                w.severity === "warning" && "bg-amber-50 dark:bg-amber-900/20 border-amber-500 text-amber-700 dark:text-amber-300",
                w.severity === "info" && "bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-700 dark:text-blue-300"
              )}
            >
              <span className="flex-shrink-0 mt-0.5">
                {w.severity === "error" && <AlertCircleIcon size={18} className="text-rose-500" />}
                {w.severity === "warning" && <AlertCircleIcon size={18} className="text-amber-500" />}
                {w.severity === "info" && <InfoIcon size={18} className="text-blue-500" />}
              </span>
              <div>
                <span className="font-medium capitalize">{w.severity}:</span>{" "}
                {w.message}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {METRIC_GROUPS.map((group) => (
          <div key={group.key} className="card animate-slide-up">
            <div className="card-header">
              <h3 className="card-title">{group.title}</h3>
            </div>
            <div className="card-body space-y-3">
              {group.metrics.map((m) => {
                const value = getNestedValue(dataMap, m.key)
                return (
                  <MetricCard
                    key={m.key}
                    label={m.label}
                    value={value}
                    format={m.format}
                    decimals={m.decimals}
                    tooltip={m.tooltipKey ? getNestedValue(dataMap, m.tooltipKey) : undefined}
                  />
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {(sentence_stats.lengths.length > 0 || comparisonData) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {sentence_stats.lengths.length > 0 && (
            <div className="card animate-slide-up">
              <div className="card-header">
                <h3 className="card-title">Sentence Length Distribution</h3>
              </div>
              <div className="card-body">
                <SentenceLengthChart lengths={sentence_stats.lengths} />
              </div>
            </div>
          )}

          {comparisonData && (
            <div className="card animate-slide-up">
              <div className="card-header">
                <h3 className="card-title">Before / After Comparison</h3>
              </div>
              <div className="card-body">
                <ComparisonChart
                  before={Object.fromEntries(Object.entries(comparisonData).map(([k, v]) => [k, v.before]))}
                  after={Object.fromEntries(Object.entries(comparisonData).map(([k, v]) => [k, v.after]))}
                  labels={Object.fromEntries(Object.entries(comparisonData).map(([k]) => [k, k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())]))}
                />
              </div>
            </div>
          )}

          {naturalness && (
            <div className="card animate-slide-up lg:col-span-2">
              <div className="card-header">
                <h3 className="card-title">Naturalness Score Components</h3>
              </div>
              <div className="card-body">
                <RadarChart
                  data={Object.entries(naturalness.components).map(([metric, value]) => ({
                    metric: metric.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
                    value: Math.round(value),
                  }))}
                />
                <p className="mt-4 text-xs text-storm-500 dark:text-storm-400 text-center">{naturalness.disclaimer}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {lexical_metrics.most_repeated_words.length > 0 && (
        <div className="card animate-slide-up">
          <div className="card-header">
            <h3 className="card-title">Most Repeated Words</h3>
          </div>
          <div className="card-body">
            <div className="flex flex-wrap gap-2">
              {lexical_metrics.most_repeated_words.slice(0, 15).map((item, i) => (
                <span
                  key={i}
                  className="badge badge-default"
                >
                  {item.word} <span className="text-storm-400 ml-1">×{item.count}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {template_phrases.template_phrases_found.length > 0 && (
        <div className="card animate-slide-up">
          <div className="card-header flex items-center justify-between">
            <h3 className="card-title">Template Phrases Detected</h3>
            <span className="badge badge-warning">{template_phrases.unique_templates_used} unique</span>
          </div>
          <div className="card-body">
            <div className="flex flex-wrap gap-2">
              {template_phrases.template_phrases_found.map((item, i) => (
                <span
                  key={i}
                  className="badge badge-warning"
                >
                  "{item.phrase}" <span className="ml-1">×{item.count}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {passive_voice.passive_examples.length > 0 && (
        <div className="card animate-slide-up">
          <div className="card-header">
            <h3 className="card-title">Passive Voice Examples</h3>
          </div>
          <div className="card-body">
            <ul className="space-y-2 text-sm text-storm-600 dark:text-storm-400 font-mono">
              {passive_voice.passive_examples.map((ex, i) => (
                <li key={i} className="p-2 rounded bg-storm-50 dark:bg-storm-900/30 border border-storm-100 dark:border-storm-800">
                  {ex}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

