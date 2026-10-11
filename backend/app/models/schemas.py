from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from app.models.enums import HumanizationStyle, HumanizationStrength


class BasicStats(BaseModel):
    character_count: int
    character_count_no_spaces: int
    word_count: int
    unique_word_count: int
    sentence_count: int
    paragraph_count: int
    avg_word_length: float
    avg_sentence_length: float


class SentenceStats(BaseModel):
    sentence_count: int
    min_length: int
    max_length: int
    mean_length: float
    median_length: float
    std_dev: float
    coefficient_of_variation: float
    lengths: List[int]


class LexicalMetrics(BaseModel):
    type_token_ratio: Optional[float]
    root_ttr: Optional[float]
    corrected_ttr: Optional[float]
    bilogarithmic_ttr: Optional[float]
    herdan_c: Optional[float]
    summer_index: Optional[float]
    lexical_density: Optional[float]
    hapax_legomena_ratio: Optional[float]
    hapax_dislegomena_ratio: Optional[float]
    unique_word_count: int
    total_word_count: int
    content_word_count: int
    function_word_count: int
    most_repeated_words: List[Dict[str, Any]]


class ReadabilityMetrics(BaseModel):
    flesch_reading_ease: Optional[float]
    flesch_kincaid_grade: Optional[float]
    gunning_fog: Optional[float]
    smog_index: Optional[float]
    automated_readability_index: Optional[float]
    coleman_liau_index: Optional[float]
    lix: Optional[float]
    rix: Optional[float]
    dale_chall_readability_score: Optional[float]


class POSDistribution(BaseModel):
    counts: Dict[str, int]
    percentages: Dict[str, float]
    total_tokens: int


class PunctuationDistribution(BaseModel):
    counts: Dict[str, int]
    percentages: Dict[str, float]
    total_punctuation: int


class ConjunctionIndicators(BaseModel):
    coordinating: int
    subordinating: int
    correlative: int
    conjunctive_adverbs: int
    total: int


class SyntaxFeatures(BaseModel):
    dependency_distribution: Dict[str, float]
    nsubj_count: int
    dobj_count: int
    prep_count: int
    advcl_count: int
    relcl_count: int
    ccomp_count: int
    xcomp_count: int


class NGramRepetition(BaseModel):
    repeated_bigrams: List[Dict[str, Any]]
    repeated_trigrams: List[Dict[str, Any]]
    bigram_repetition_ratio: float
    trigram_repetition_ratio: float
    total_bigrams: int
    total_trigrams: int
    unique_bigrams: int
    unique_trigrams: int


class TemplatePhraseMetrics(BaseModel):
    template_phrases_found: List[Dict[str, Any]]
    total_template_occurrences: int
    template_phrase_density: float
    unique_templates_used: int


class PassiveVoiceMetrics(BaseModel):
    passive_sentences: int
    total_sentences: int
    passive_ratio: float
    passive_examples: List[str]
    note: str


class AnalysisResult(BaseModel):
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


class NaturalnessScore(BaseModel):
    score: float
    components: Dict[str, float]
    interpretation: str
    disclaimer: str


class Warning(BaseModel):
    type: str
    message: str
    severity: str = "warning"


# Request/Response Models

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    include_details: bool = True


class AnalyzeResponse(BaseModel):
    request_id: str
    analysis: AnalysisResult
    naturalness_score: Optional[NaturalnessScore] = None
    warnings: List[Warning] = []
    processing_time_ms: float


class HumanizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    style: HumanizationStyle = HumanizationStyle.NATURAL
    strength: HumanizationStrength = HumanizationStrength.MEDIUM
    preserve_formatting: bool = True


class HumanizeResponse(BaseModel):
    request_id: str
    original_text: str
    humanized_text: str
    style: HumanizationStyle
    strength: HumanizationStrength
    semantic_similarity: Optional[float] = None
    content_preservation_warnings: List[Warning] = []
    processing_time_ms: float
    model_info: Dict[str, Any]


class CompareRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    style: HumanizationStyle = HumanizationStyle.NATURAL
    strength: HumanizationStrength = HumanizationStrength.MEDIUM


class CompareResponse(BaseModel):
    request_id: str
    original_analysis: AnalysisResult
    humanized_analysis: AnalysisResult
    humanized_text: str
    semantic_similarity: float
    naturalness_score_before: NaturalnessScore
    naturalness_score_after: NaturalnessScore
    metric_comparison: Dict[str, Any]
    content_preservation_warnings: List[Warning] = []
    processing_time_ms: float
    model_info: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
    device: str
    gpu_available: bool
    gpu_memory_used_mb: Optional[int] = None
    gpu_memory_total_mb: Optional[int] = None


class ModelInfo(BaseModel):
    name: str
    provider: str
    device: str
    loaded: bool
    quantization: Optional[str] = None


class ModelsResponse(BaseModel):
    current: ModelInfo
    available: List[ModelInfo]