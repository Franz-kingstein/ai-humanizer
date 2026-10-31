import time
import uuid
import logging
from typing import Optional
from dataclasses import dataclass

from app.services.analyzer import TextAnalyzer, get_analyzer
from app.services.humanizer import get_humanizer, Humanizer
from app.services.semantic_validator import get_semantic_validator, SemanticValidator
from app.services.preprocessing import check_content_preservation, ContentPreservationResult
from app.services.metrics import calculate_naturalness_score, NaturalnessScore
from app.models.schemas import (
    AnalysisResult, NaturalnessScore as NaturalnessScoreSchema,
    Warning, HumanizeResponse, CompareResponse
)
from app.models.enums import HumanizationStyle, HumanizationStrength
from app.config import get_settings


logger = logging.getLogger(__name__)


def _dedupe_warnings(warnings: list) -> list:
    """Remove duplicate warnings (same type + message), preserving order."""
    seen = set()
    unique = []
    for w in warnings:
        key = (w.type, w.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(w)
    return unique


@dataclass
class PipelineResult:
    """Complete pipeline result."""
    request_id: str
    original_text: str
    humanized_text: str
    original_analysis: AnalysisResult
    humanized_analysis: AnalysisResult
    semantic_similarity: float
    naturalness_before: NaturalnessScore
    naturalness_after: NaturalnessScore
    content_preservation: ContentPreservationResult
    warnings: list
    processing_time_ms: float
    model_info: dict


class HumanizationPipeline:
    """Main orchestration pipeline."""

    def __init__(self, settings=None, nlp=None):
        self.settings = settings or get_settings()
        self.analyzer = get_analyzer(nlp)
        self.humanizer = get_humanizer(settings=self.settings)
        self.semantic_validator = get_semantic_validator(self.settings)

    def analyze(self, text: str, request_id: str = None) -> tuple:
        """Analyze text only."""
        request_id = request_id or str(uuid.uuid4())[:8]
        start_time = time.time()

        analysis = self.analyzer.analyze(text)
        naturalness = calculate_naturalness_score(analysis, text)
        processing_time = (time.time() - start_time) * 1000

        return analysis, naturalness, processing_time, request_id

    def humanize(
        self,
        text: str,
        style: HumanizationStyle,
        strength: HumanizationStrength,
        request_id: str = None,
    ) -> HumanizeResponse:
        """Humanize text with validation."""
        request_id = request_id or str(uuid.uuid4())[:8]
        start_time = time.time()

        # Humanize
        result = self.humanizer.humanize(text, style, strength)

        # Content preservation check
        preservation = check_content_preservation(text, result.text)

        # Semantic validation
        similarity, is_valid, sem_warning = self.semantic_validator.validate(text, result.text)

        warnings = preservation.warnings.copy()
        if sem_warning:
            warnings.append(Warning(type="semantic_similarity", message=sem_warning, severity="warning"))

        processing_time = (time.time() - start_time) * 1000

        return HumanizeResponse(
            request_id=request_id,
            original_text=text,
            humanized_text=result.text,
            style=style,
            strength=strength,
            semantic_similarity=similarity,
            content_preservation_warnings=warnings,
            processing_time_ms=processing_time,
            model_info=result.model_info,
        )

    def compare(
        self,
        text: str,
        style: HumanizationStyle,
        strength: HumanizationStrength,
        request_id: str = None,
    ) -> CompareResponse:
        """Full pipeline: analyze -> humanize -> validate -> compare."""
        request_id = request_id or str(uuid.uuid4())[:8]
        start_time = time.time()

        try:
            # Original analysis
            original_analysis = self.analyzer.analyze(text)
            naturalness_before = calculate_naturalness_score(original_analysis, text)

            # Humanize with retries
            best_result = None
            best_similarity = 0.0
            all_warnings = []

            for attempt in range(self.settings.max_rewrite_attempts + 1):
                result = self.humanizer.humanize(text, style, strength)

                # Content preservation
                preservation = check_content_preservation(text, result.text)

                # Semantic validation
                similarity, is_valid, sem_warning = self.semantic_validator.validate(text, result.text)

                attempt_warnings = preservation.warnings.copy()
                if sem_warning:
                    attempt_warnings.append(Warning(type="semantic_similarity", message=sem_warning, severity="warning"))

                logger.info(f"Attempt {attempt + 1}: similarity={similarity:.3f}, valid={is_valid}")

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_result = result
                    all_warnings = attempt_warnings

                if is_valid:
                    break

            # Use best result
            humanized_text = best_result.text
            model_info = best_result.model_info

            # Analyze humanized text
            humanized_analysis = self.analyzer.analyze(humanized_text)
            naturalness_after = calculate_naturalness_score(humanized_analysis, humanized_text)

            # Final content preservation check.
            # Retry attempts already appended their own warnings, so drop
            # duplicates rather than reporting the same issue several times.
            final_preservation = check_content_preservation(text, humanized_text)
            all_warnings.extend(final_preservation.warnings)
            all_warnings = _dedupe_warnings(all_warnings)

            # Metric comparison
            metric_comparison = self._compare_metrics(original_analysis, humanized_analysis, naturalness_before, naturalness_after)

            processing_time = (time.time() - start_time) * 1000

            return CompareResponse(
            request_id=request_id,
            original_analysis=original_analysis.to_dict(),
            humanized_analysis=humanized_analysis.to_dict(),
            humanized_text=humanized_text,
            semantic_similarity=best_similarity,
            naturalness_score_before=NaturalnessScoreSchema(
                score=naturalness_before.score,
                components=naturalness_before.components,
                interpretation=naturalness_before.interpretation,
                disclaimer=naturalness_before.disclaimer,
            ),
            naturalness_score_after=NaturalnessScoreSchema(
                score=naturalness_after.score,
                components=naturalness_after.components,
                interpretation=naturalness_after.interpretation,
                disclaimer=naturalness_after.disclaimer,
            ),
            metric_comparison=metric_comparison,
            content_preservation_warnings=all_warnings,
            processing_time_ms=processing_time,
            model_info=model_info,
        )
        except Exception as e:
            logger.error(f"Error in compare pipeline: {e}", exc_info=True)
            raise

    def _compare_metrics(self, before: AnalysisResult, after: AnalysisResult, naturalness_before: NaturalnessScore, naturalness_after: NaturalnessScore) -> dict:
        """Compare metrics before and after."""
        return {
            "basic_stats": {
                "word_count": {
                    "before": before.basic_stats.word_count,
                    "after": after.basic_stats.word_count,
                    "change": after.basic_stats.word_count - before.basic_stats.word_count,
                },
                "sentence_count": {
                    "before": before.basic_stats.sentence_count,
                    "after": after.basic_stats.sentence_count,
                    "change": after.basic_stats.sentence_count - before.basic_stats.sentence_count,
                },
                "avg_sentence_length": {
                    "before": before.basic_stats.avg_sentence_length,
                    "after": after.basic_stats.avg_sentence_length,
                    "change": round(after.basic_stats.avg_sentence_length - before.basic_stats.avg_sentence_length, 2),
                },
            },
            "lexical_diversity": {
                "type_token_ratio": {
                    "before": before.lexical_metrics.type_token_ratio,
                    "after": after.lexical_metrics.type_token_ratio,
                    "change": round(
                        (after.lexical_metrics.type_token_ratio or 0) - (before.lexical_metrics.type_token_ratio or 0), 4
                    ),
                },
            },
            "readability": {
                "flesch_reading_ease": {
                    "before": before.readability.flesch_reading_ease,
                    "after": after.readability.flesch_reading_ease,
                    "change": round(
                        (after.readability.flesch_reading_ease or 0) - (before.readability.flesch_reading_ease or 0), 2
                    ),
                },
            },
            "repetition": {
                "bigram_repetition_ratio": {
                    "before": before.ngram_repetition.bigram_repetition_ratio,
                    "after": after.ngram_repetition.bigram_repetition_ratio,
                    "change": round(
                        after.ngram_repetition.bigram_repetition_ratio - before.ngram_repetition.bigram_repetition_ratio, 4
                    ),
                },
            },
            "template_phrases": {
                "template_phrase_density": {
                    "before": before.template_phrases.template_phrase_density,
                    "after": after.template_phrases.template_phrase_density,
                    "change": round(
                        after.template_phrases.template_phrase_density - before.template_phrases.template_phrase_density, 2
                    ),
                },
            },
            "passive_voice": {
                "passive_ratio": {
                    "before": before.passive_voice.passive_ratio,
                    "after": after.passive_voice.passive_ratio,
                    "change": round(
                        after.passive_voice.passive_ratio - before.passive_voice.passive_ratio, 4
                    ),
                },
            },
            "naturalness_score": {
                "before": naturalness_before.score,
                "after": naturalness_after.score,
                "change": round(naturalness_after.score - naturalness_before.score, 2),
            },
        }


_pipeline: Optional[HumanizationPipeline] = None


def get_pipeline(settings=None, nlp=None) -> HumanizationPipeline:
    """Factory function returning a process-wide pipeline singleton.

    The pipeline owns the humanizer model and semantic model, so it must be
    created exactly once and reused across requests. Creating a new instance
    per request would reload the transformer weights every call.
    """
    global _pipeline
    if _pipeline is None:
        # Load spaCy here (once) so syntax/passive-voice metrics are populated.
        if nlp is None:
            try:
                import spacy
                from app.config import get_settings as _gs
                nlp = spacy.load(_gs().spacy_model)
            except Exception as e:
                logger.warning(f"spaCy unavailable in pipeline: {e}")
                nlp = None
        _pipeline = HumanizationPipeline(settings, nlp)
    return _pipeline


def reset_pipeline() -> None:
    """Drop the cached pipeline (used by tests)."""
    global _pipeline
    _pipeline = None