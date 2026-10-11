"use client"

import { AnalysisResult, NaturalnessScore, Warning } from "@/lib/types"
import { MetricCard } from "./MetricCard"
import { cn, formatNumber, formatPercent, formatRatio, getReadabilityLabel } from "@/lib/utils"
import { SentenceLengthChart, ComparisonChart, RadarChart } from "./Charts"

interface AnalysisDisplayProps {
  analysis: AnalysisResult
  naturalness?: NaturalnessScore
  warnings?: Warning[]
  title?: string
  comparisonData?: Record<string, { before: number; after: number }>
}

export function AnalysisDisplay({
  analysis,
  naturalness,
  warnings = [],
  title = "Analysis Results",
  comparisonData,
}: AnalysisDisplayProps) {
  const { basic_stats, sentence_stats, lexical_metrics, readability, ngram_repetition, template_phrases, passive_voice } = analysis

  const metricGroups = [
    {
      title: "Basic Statistics",
      metrics: [
        { label: "Words", value: basic_stats.word_count, format: "number" as const },
        { label: "Unique Words", value: basic_stats.unique_word_count, format: "number" as const },
        { label: "Sentences", value: basic_stats.sentence_count, format: "number" as const },
        { label: "Paragraphs", value: basic_stats.paragraph_count, format: "number" as const },
        { label: "Avg Word Length", value: basic_stats.avg_word_length, format: "number" as const, decimals: 1 },
        { label: "Avg Sentence Length", value: basic_stats.avg_sentence_length, format: "number" as const, decimals: 1 },
      ],
    },
    {
      title: "Sentence Structure",
      metrics: [
        { label: "Min Length", value: sentence_stats.min_length, format: "number" as const },
        { label: "Max Length", value: sentence_stats.max_length, format: "number" as const },
        { label: "Mean Length", value: sentence_stats.mean_length, format: "number" as const, decimals: 1 },
        { label: "Median Length", value: sentence_stats.median_length, format: "number" as const, decimals: 1 },
        { label: "Std Deviation", value: sentence_stats.std_dev, format: "number" as const, decimals: 1 },
        { label: "Coeff. of Variation", value: sentence_stats.coefficient_of_variation, format: "ratio" as const },
      ],
    },
    {
      title: "Lexical Diversity",
      metrics: [
        { label: "Type-Token Ratio", value: lexical_metrics.type_token_ratio, format: "ratio" as const },
        { label: "Root TTR (Guiraud)", value: lexical_metrics.root_ttr, format: "ratio" as const },
        { label: "Herdan's C", value: lexical_metrics.herdan_c, format: "ratio" as const },
        { label: "Lexical Density", value: lexical_metrics.lexical_density, format: "percent" as const, decimals: 1 },
        { label: "Hapax Legomena Ratio", value: lexical_metrics.hapax_legomena_ratio, format: "ratio" as const },
        { label: "Repeated Words", value: lexical_metrics.most_repeated_words.length, format: "number" as const },
      ],
    },
    {
      title: "Readability",
      metrics: [
        { label: "Flesch Reading Ease", value: readability.flesch_reading_ease, format: "number" as const, decimals: 1, tooltip: getReadabilityLabel(readability.flesch_reading_ease) },
        { label: "Flesch-Kincaid Grade", value: readability.flesch_kincaid_grade, format: "number" as const, decimals: 1 },
        { label: "Gunning Fog", value: readability.gunning_fog, format: "number" as const, decimals: 1 },
        { label: "SMOG Index", value: readability.smog_index, format: "number" as const, decimals: 1 },
        { label: "Automated Readability", value: readability.automated_readability_index, format: "number" as const, decimals: 1 },
        { label: "Coleman-Liau", value: readability.coleman_liau_index, format: "number" as const, decimals: 1 },
      ],
    },
    {
      title: "Repetition & Templates",
      metrics: [
        { label: "Bigram Repetition", value: ngram_repetition.bigram_repetition_ratio, format: "ratio" as const },
        { label: "Trigram Repetition", value: ngram_repetition.trigram_repetition_ratio, format: "ratio" as const },
        { label: "Unique Bigrams", value: ngram_repetition.unique_bigrams, format: "number" as const },
        { label: "Unique Trigrams", value: ngram_repetition.unique_trigrams, format: "number" as const },
        { label: "Template Density (per 1k)", value: template_phrases.template_phrase_density, format: "number" as const, decimals: 1 },
        { label: "Templates Used", value: template_phrases.unique_templates_used, format: "number" as const },
      ],
    },
    {
      title: "Passive Voice",
      metrics: [
        { label: "Passive Sentences", value: passive_voice.passive_sentences, format: "number" as const },
        { label: "Total Sentences", value: passive_voice.total_sentences, format: "number" as const },
        { label: "Passive Ratio", value: passive_voice.passive_ratio, format: "percent" as const, decimals: 1 },
      ],
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
        {naturalness && (
          <MetricCard
            label="Naturalness Score"
            value={naturalness.score}
            format="score"
            className="min-w-[200px]"
          />
        )}
      </div>

      {warnings.length > 0 && (
        <div className="space-y-2">
          {warnings.map((w, i) => (
            <div
              key={i}
              className={cn(
                "p-3 rounded-lg text-sm border-l-4",
                w.severity === "error" && "bg-red-50 dark:bg-red-900/30 border-red-500 text-red-700 dark:text-red-300",
                w.severity === "warning" && "bg-yellow-50 dark:bg-yellow-900/30 border-yellow-500 text-yellow-700 dark:text-yellow-300",
                w.severity === "info" && "bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-700 dark:text-blue-300"
              )}
            >
              <span className="font-medium capitalize">{w.severity}:</span> {w.message}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metricGroups.map((group, gi) => (
          <div key={gi} className="space-y-3 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 pb-2">
              {group.title}
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {group.metrics.map((m, mi) => (
                <MetricCard
                  key={mi}
                  label={m.label}
                  value={m.value}
                  format={m.format}
                  decimals={m.decimals}
                  tooltip={(m as any).tooltip}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {(sentence_stats.lengths.length > 0 || comparisonData) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {sentence_stats.lengths.length > 0 && (
            <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Sentence Length Distribution</h3>
              <SentenceLengthChart lengths={sentence_stats.lengths} />
            </div>
          )}

          {comparisonData && (
            <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Before / After Comparison</h3>
              <ComparisonChart
                before={Object.fromEntries(Object.entries(comparisonData).map(([k, v]) => [k, v.before]))}
                after={Object.fromEntries(Object.entries(comparisonData).map(([k, v]) => [k, v.after]))}
                labels={Object.fromEntries(Object.entries(comparisonData).map(([k]) => [k, k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())]))}
              />
            </div>
          )}

          {naturalness && (
            <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 lg:col-span-2">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Naturalness Score Components</h3>
              <RadarChart
                data={Object.entries(naturalness.components).map(([metric, value]) => ({
                  metric: metric.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
                  value: Math.round(value),
                }))}
              />
              <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">{naturalness.disclaimer}</p>
            </div>
          )}
        </div>
      )}

      {lexical_metrics.most_repeated_words.length > 0 && (
        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Most Repeated Words</h3>
          <div className="flex flex-wrap gap-2">
            {lexical_metrics.most_repeated_words.slice(0, 15).map((item, i) => (
              <span
                key={i}
                className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded"
              >
                {item.word} ({item.count})
              </span>
            ))}
          </div>
        </div>
      )}

      {template_phrases.template_phrases_found.length > 0 && (
        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Template Phrases Detected</h3>
          <div className="flex flex-wrap gap-2">
            {template_phrases.template_phrases_found.map((item, i) => (
              <span
                key={i}
                className="px-2 py-1 text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded"
              >
                "{item.phrase}" ×{item.count}
              </span>
            ))}
          </div>
        </div>
      )}

      {passive_voice.passive_examples.length > 0 && (
        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Passive Voice Examples</h3>
          <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
            {passive_voice.passive_examples.map((ex, i) => (
              <li key={i} className="font-mono bg-gray-100 dark:bg-gray-900 p-2 rounded">{ex}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}