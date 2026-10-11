export interface BasicStats {
  character_count: number
  character_count_no_spaces: number
  word_count: number
  unique_word_count: number
  sentence_count: number
  paragraph_count: number
  avg_word_length: number
  avg_sentence_length: number
}

export interface SentenceStats {
  sentence_count: number
  min_length: number
  max_length: number
  mean_length: number
  median_length: number
  std_dev: number
  coefficient_of_variation: number
  lengths: number[]
}

export interface LexicalMetrics {
  type_token_ratio: number | null
  root_ttr: number | null
  corrected_ttr: number | null
  bilogarithmic_ttr: number | null
  herdan_c: number | null
  summer_index: number | null
  lexical_density: number | null
  hapax_legomena_ratio: number | null
  hapax_dislegomena_ratio: number | null
  unique_word_count: number
  total_word_count: number
  content_word_count: number
  function_word_count: number
  most_repeated_words: Array<{ word: string; count: number }>
}

export interface ReadabilityMetrics {
  flesch_reading_ease: number | null
  flesch_kincaid_grade: number | null
  gunning_fog: number | null
  smog_index: number | null
  automated_readability_index: number | null
  coleman_liau_index: number | null
  lix: number | null
  rix: number | null
  dale_chall_readability_score: number | null
}

export interface POSDistribution {
  counts: Record<string, number>
  percentages: Record<string, number>
  total_tokens: number
}

export interface PunctuationDistribution {
  counts: Record<string, number>
  percentages: Record<string, number>
  total_punctuation: number
}

export interface ConjunctionIndicators {
  coordinating: number
  subordinating: number
  correlative: number
  conjunctive_adverbs: number
  total: number
}

export interface SyntaxFeatures {
  dependency_distribution: Record<string, number>
  nsubj_count: number
  dobj_count: number
  prep_count: number
  advcl_count: number
  relcl_count: number
  ccomp_count: number
  xcomp_count: number
}

export interface NGramRepetition {
  repeated_bigrams: Array<{ ngram: string; count: number }>
  repeated_trigrams: Array<{ ngram: string; count: number }>
  bigram_repetition_ratio: number
  trigram_repetition_ratio: number
  total_bigrams: number
  total_trigrams: number
  unique_bigrams: number
  unique_trigrams: number
}

export interface TemplatePhraseMetrics {
  template_phrases_found: Array<{ phrase: string; count: number }>
  total_template_occurrences: number
  template_phrase_density: number
  unique_templates_used: number
}

export interface PassiveVoiceMetrics {
  passive_sentences: number
  total_sentences: number
  passive_ratio: number
  passive_examples: string[]
  note: string
}

export interface AnalysisResult {
  basic_stats: BasicStats
  sentence_stats: SentenceStats
  lexical_metrics: LexicalMetrics
  readability: ReadabilityMetrics
  pos_distribution: POSDistribution
  punctuation_distribution: PunctuationDistribution
  conjunction_indicators: ConjunctionIndicators
  syntax_features: SyntaxFeatures
  ngram_repetition: NGramRepetition
  template_phrases: TemplatePhraseMetrics
  passive_voice: PassiveVoiceMetrics
}

export interface NaturalnessScore {
  score: number
  components: Record<string, number>
  interpretation: string
  disclaimer: string
}

export interface Warning {
  type: string
  message: string
  severity: "info" | "warning" | "error"
}

export interface AnalyzeResponse {
  request_id: string
  analysis: AnalysisResult
  naturalness_score?: NaturalnessScore
  warnings: Warning[]
  processing_time_ms: number
}

export interface HumanizeResponse {
  request_id: string
  original_text: string
  humanized_text: string
  style: string
  strength: string
  semantic_similarity: number | null
  content_preservation_warnings: Warning[]
  processing_time_ms: number
  model_info: Record<string, unknown>
}

export interface CompareResponse {
  request_id: string
  original_analysis: AnalysisResult
  humanized_analysis: AnalysisResult
  humanized_text: string
  semantic_similarity: number
  naturalness_score_before: NaturalnessScore
  naturalness_score_after: NaturalnessScore
  metric_comparison: Record<string, unknown>
  content_preservation_warnings: Warning[]
  processing_time_ms: number
  model_info: Record<string, unknown>
}

export type HumanizationStyle = "natural" | "academic" | "professional" | "casual" | "technical"
export type HumanizationStrength = "low" | "medium" | "high"

export interface HealthResponse {
  status: string
  version: string
  model_loaded: boolean
  device: string
  gpu_available: boolean
  gpu_memory_used_mb: number | null
  gpu_memory_total_mb: number | null
}

export interface ModelInfo {
  name: string
  provider: string
  device: string
  loaded: boolean
  quantization?: string
}

export interface ModelsResponse {
  current: ModelInfo
  available: ModelInfo[]
}