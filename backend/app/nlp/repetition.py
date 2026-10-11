from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import re


@dataclass
class NGramRepetition:
    """N-gram repetition analysis results."""
    bigrams: Dict[str, int]
    trigrams: Dict[str, int]
    repeated_bigrams: List[Dict[str, int]]
    repeated_trigrams: List[Dict[str, int]]
    bigram_repetition_ratio: float
    trigram_repetition_ratio: float
    total_bigrams: int
    total_trigrams: int
    unique_bigrams: int
    unique_trigrams: int

    def to_dict(self) -> dict:
        return {
            "repeated_bigrams": self.repeated_bigrams,
            "repeated_trigrams": self.repeated_trigrams,
            "bigram_repetition_ratio": self.bigram_repetition_ratio,
            "trigram_repetition_ratio": self.trigram_repetition_ratio,
            "total_bigrams": self.total_bigrams,
            "total_trigrams": self.total_trigrams,
            "unique_bigrams": self.unique_bigrams,
            "unique_trigrams": self.unique_trigrams,
        }


@dataclass
class TemplatePhraseMetrics:
    """Template phrase density analysis."""
    template_phrases_found: List[Dict[str, int]]
    total_template_occurrences: int
    template_phrase_density: float  # per 1000 words
    unique_templates_used: int

    def to_dict(self) -> dict:
        return {
            "template_phrases_found": self.template_phrases_found,
            "total_template_occurrences": self.total_template_occurrences,
            "template_phrase_density": self.template_phrase_density,
            "unique_templates_used": self.unique_templates_used,
        }


# Default template phrases (configurable)
DEFAULT_TEMPLATE_PHRASES = [
    "moreover",
    "furthermore",
    "additionally",
    "in conclusion",
    "it is important to note that",
    "it is worth noting that",
    "in today's rapidly evolving world",
    "in today's world",
    "this highlights the importance",
    "a key aspect is",
    "in summary",
    "to summarize",
    "it should be noted that",
    "it is worth mentioning that",
    "plays a crucial role",
    "plays an important role",
    "delve into",
    "tapestry",
    "landscape",
    "realm",
    "unleash",
    "unlock",
    "revolutionize",
    "game-changer",
    "cutting-edge",
    "paradigm shift",
    "holistic approach",
    "at the end of the day",
    "when it comes to",
    "it is essential to",
    "it is crucial to",
    "it is vital to",
    "bear in mind",
    "take into account",
    "in terms of",
    "with regard to",
    "as a matter of fact",
    "needless to say",
    "last but not least",
]


def extract_ngrams(words: List[str], n: int) -> List[Tuple[str, ...]]:
    """Extract n-grams from word list."""
    if len(words) < n:
        return []
    return [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]


def analyze_ngram_repetition(words: List[str]) -> NGramRepetition:
    """Analyze n-gram repetition patterns."""
    if len(words) < 2:
        return NGramRepetition(
            bigrams={},
            trigrams={},
            repeated_bigrams=[],
            repeated_trigrams=[],
            bigram_repetition_ratio=0.0,
            trigram_repetition_ratio=0.0,
            total_bigrams=0,
            total_trigrams=0,
            unique_bigrams=0,
            unique_trigrams=0,
        )

    # Extract bigrams and trigrams
    bigrams = extract_ngrams(words, 2)
    trigrams = extract_ngrams(words, 3)

    bigram_strings = [" ".join(bg) for bg in bigrams]
    trigram_strings = [" ".join(tg) for tg in trigrams]

    bigram_counts = Counter(bigram_strings)
    trigram_counts = Counter(trigram_strings)

    total_bigrams = len(bigram_strings)
    total_trigrams = len(trigram_strings)
    unique_bigrams = len(bigram_counts)
    unique_trigrams = len(trigram_counts)

    # Repeated n-grams (count > 1)
    repeated_bigrams = [
        {"ngram": ngram, "count": count}
        for ngram, count in bigram_counts.most_common()
        if count > 1
    ]
    repeated_trigrams = [
        {"ngram": ngram, "count": count}
        for ngram, count in trigram_counts.most_common()
        if count > 1
    ]

    # Repetition ratios
    bigram_repetition_ratio = 0.0
    if total_bigrams > 0:
        repeated_bigram_tokens = sum(bg["count"] for bg in repeated_bigrams)
        bigram_repetition_ratio = round(repeated_bigram_tokens / total_bigrams, 4)

    trigram_repetition_ratio = 0.0
    if total_trigrams > 0:
        repeated_trigram_tokens = sum(tg["count"] for tg in repeated_trigrams)
        trigram_repetition_ratio = round(repeated_trigram_tokens / total_trigrams, 4)

    return NGramRepetition(
        bigrams=dict(bigram_counts),
        trigrams=dict(trigram_counts),
        repeated_bigrams=repeated_bigrams,
        repeated_trigrams=repeated_trigrams,
        bigram_repetition_ratio=bigram_repetition_ratio,
        trigram_repetition_ratio=trigram_repetition_ratio,
        total_bigrams=total_bigrams,
        total_trigrams=total_trigrams,
        unique_bigrams=unique_bigrams,
        unique_trigrams=unique_trigrams,
    )


def analyze_template_phrases(
    text: str,
    template_phrases: Optional[List[str]] = None
) -> TemplatePhraseMetrics:
    """Analyze template phrase density."""
    if template_phrases is None:
        template_phrases = DEFAULT_TEMPLATE_PHRASES

    text_lower = text.lower()
    word_count = len(re.findall(r'\b\w+\b', text))

    found_phrases = []
    total_occurrences = 0

    for phrase in template_phrases:
        # Count occurrences (case-insensitive)
        count = len(re.findall(re.escape(phrase.lower()), text_lower))
        if count > 0:
            found_phrases.append({"phrase": phrase, "count": count})
            total_occurrences += count

    # Density per 1000 words
    density = (total_occurrences / word_count * 1000) if word_count > 0 else 0.0

    return TemplatePhraseMetrics(
        template_phrases_found=found_phrases,
        total_template_occurrences=total_occurrences,
        template_phrase_density=round(density, 2),
        unique_templates_used=len(found_phrases),
    )