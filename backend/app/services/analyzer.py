import re
import spacy
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from app.nlp.tokenizer import TextTokenizer, simple_sentence_split, simple_word_tokenize
from app.nlp.pos import (
    analyze_pos, analyze_punctuation, analyze_conjunctions, get_syntax_features,
    POSDistribution, PunctuationDistribution, ConjunctionIndicators
)
from app.nlp.readability import calculate_readability, ReadabilityMetrics
from app.nlp.lexical import calculate_lexical_metrics, LexicalMetrics
from app.nlp.repetition import (
    analyze_ngram_repetition, analyze_template_phrases,
    NGramRepetition, TemplatePhraseMetrics
)
from app.nlp.dependency import analyze_passive_voice, PassiveVoiceMetrics
from app.nlp.tokenizer import calculate_basic_stats, calculate_sentence_stats, BasicStatistics, SentenceStatistics
from app.config import get_settings


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    basic_stats: BasicStatistics
    sentence_stats: SentenceStatistics
    lexical_metrics: LexicalMetrics
    readability: ReadabilityMetrics
    pos_distribution: POSDistribution
    punctuation_distribution: PunctuationDistribution
    conjunction_indicators: ConjunctionIndicators
    syntax_features: Dict[str, Any]
    ngram_repetition: NGramRepetition
    template_phrases: TemplatePhraseMetrics
    passive_voice: PassiveVoiceMetrics

    def to_dict(self) -> dict:
        return {
            "basic_stats": self.basic_stats.to_dict(),
            "sentence_stats": self.sentence_stats.to_dict(),
            "lexical_metrics": self.lexical_metrics.to_dict(),
            "readability": self.readability.to_dict(),
            "pos_distribution": self.pos_distribution.to_dict(),
            "punctuation_distribution": self.punctuation_distribution.to_dict(),
            "conjunction_indicators": self.conjunction_indicators.to_dict(),
            "syntax_features": self.syntax_features,
            "ngram_repetition": self.ngram_repetition.to_dict(),
            "template_phrases": self.template_phrases.to_dict(),
            "passive_voice": self.passive_voice.to_dict(),
        }


class TextAnalyzer:
    """Main text analysis orchestrator."""

    def __init__(self, nlp: Optional[spacy.Language] = None, settings=None):
        self.settings = settings or get_settings()
        self.nlp = nlp
        self.tokenizer = None
        if nlp:
            self.tokenizer = TextTokenizer(nlp, self.settings.use_stopwords_in_metrics)

    def _get_words_and_sentences(self, text: str, doc) -> tuple:
        """Extract words and sentences from text/doc."""
        if self.tokenizer:
            words = self.tokenizer.get_words(doc)
            sentences = self.tokenizer.get_sentences(doc)
            paragraphs = self.tokenizer.get_paragraphs(text)
        else:
            words = simple_word_tokenize(text)
            sentences = simple_sentence_split(text)
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        return words, sentences, paragraphs

    def _get_content_function_words(self, doc, words: List[str]) -> tuple:
        """Separate content and function words."""
        if not self.nlp:
            # Fallback: treat all as content words
            return words, []

        content_pos = {"NOUN", "VERB", "ADJ", "ADV", "PROPN"}
        content_words = []
        function_words = []

        for token in doc:
            if not token.is_alpha or token.is_space:
                continue
            word = token.text.lower()
            if token.pos_ in content_pos:
                content_words.append(word)
            else:
                function_words.append(word)

        return content_words, function_words

    def _get_words_per_sentence(self, sentences: List[str]) -> List[int]:
        """Count words per sentence."""
        if self.tokenizer and self.nlp:
            counts = []
            for sent_text in sentences:
                sent_doc = self.nlp(sent_text)
                counts.append(len(self.tokenizer.get_words(sent_doc)))
            return counts
        else:
            return [len(simple_word_tokenize(s)) for s in sentences]

    def analyze(self, text: str) -> AnalysisResult:
        """Perform complete text analysis."""
        if not text or not text.strip():
            return self._empty_result()

        # Process with spaCy if available
        doc = self.nlp(text) if self.nlp else None

        # Extract words, sentences, paragraphs
        words, sentences, paragraphs = self._get_words_and_sentences(text, doc)

        # Content/function word separation
        content_words, function_words = self._get_content_function_words(doc, words) if doc else (words, [])

        # Unique word count
        unique_words = len(set(words))

        # Words per sentence
        words_per_sentence = self._get_words_per_sentence(sentences)

        # Basic statistics
        basic_stats = calculate_basic_stats(text, words, sentences, paragraphs, unique_words)

        # Sentence statistics
        sentence_stats = calculate_sentence_stats(sentences, words_per_sentence)

        # Lexical metrics
        lexical_metrics = calculate_lexical_metrics(words, content_words, function_words)

        # Readability
        readability = calculate_readability(text)

        # POS analysis (if spaCy available)
        if doc:
            pos_distribution = analyze_pos(doc)
            punctuation_distribution = analyze_punctuation(doc)
            conjunction_indicators = analyze_conjunctions(doc)
            syntax_features = get_syntax_features(doc)
            passive_voice = analyze_passive_voice(doc)
        else:
            pos_distribution = POSDistribution({}, {}, 0)
            punctuation_distribution = PunctuationDistribution({}, {}, 0)
            conjunction_indicators = ConjunctionIndicators(0, 0, 0, 0, 0)
            syntax_features = {}
            passive_voice = PassiveVoiceMetrics(0, len(sentences), 0.0, [], "")

        # N-gram repetition
        ngram_repetition = analyze_ngram_repetition(words)

        # Template phrases
        template_phrases = analyze_template_phrases(text)

        return AnalysisResult(
            basic_stats=basic_stats,
            sentence_stats=sentence_stats,
            lexical_metrics=lexical_metrics,
            readability=readability,
            pos_distribution=pos_distribution,
            punctuation_distribution=punctuation_distribution,
            conjunction_indicators=conjunction_indicators,
            syntax_features=syntax_features,
            ngram_repetition=ngram_repetition,
            template_phrases=template_phrases,
            passive_voice=passive_voice,
        )

    def _empty_result(self) -> AnalysisResult:
        """Return empty analysis result."""
        return AnalysisResult(
            basic_stats=BasicStatistics(0, 0, 0, 0, 0, 0, 0.0, 0.0),
            sentence_stats=SentenceStatistics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, []),
            lexical_metrics=LexicalMetrics(
                None, None, None, None, None, None, None, None, None,
                0, 0, 0, 0, []
            ),
            readability=calculate_readability(""),
            pos_distribution=POSDistribution({}, {}, 0),
            punctuation_distribution=PunctuationDistribution({}, {}, 0),
            conjunction_indicators=ConjunctionIndicators(0, 0, 0, 0, 0),
            syntax_features={},
            ngram_repetition=NGramRepetition(
                {}, {}, [], [], 0.0, 0.0, 0, 0, 0, 0
            ),
            template_phrases=TemplatePhraseMetrics([], 0, 0.0, 0),
            passive_voice=PassiveVoiceMetrics(0, 0, 0.0, [], ""),
        )


def get_analyzer(nlp: Optional[spacy.Language] = None) -> TextAnalyzer:
    """Factory function to get analyzer."""
    return TextAnalyzer(nlp)