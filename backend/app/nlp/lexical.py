from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Optional
import math


@dataclass
class LexicalMetrics:
    """Lexical diversity and richness metrics."""
    type_token_ratio: Optional[float]
    root_ttr: Optional[float]  # sqrt(TTR)
    corrected_ttr: Optional[float]  # TTR * 100 / sqrt(2 * tokens)
    bilogarithmic_ttr: Optional[float]  # log(types) / log(tokens)
    herdan_c: Optional[float]  # log(types) / log(tokens)
    summer_index: Optional[float]  # log(log(types)) / log(log(tokens))
    lexical_density: Optional[float]  # content words / total words
    hapax_legomena_ratio: Optional[float]  # words appearing once / total types
    hapax_dislegomena_ratio: Optional[float]  # words appearing twice / total types
    unique_word_count: int
    total_word_count: int
    content_word_count: int
    function_word_count: int
    most_repeated_words: List[Dict[str, int]]

    def to_dict(self) -> dict:
        return {
            "type_token_ratio": self.type_token_ratio,
            "root_ttr": self.root_ttr,
            "corrected_ttr": self.corrected_ttr,
            "bilogarithmic_ttr": self.bilogarithmic_ttr,
            "herdan_c": self.herdan_c,
            "summer_index": self.summer_index,
            "lexical_density": self.lexical_density,
            "hapax_legomena_ratio": self.hapax_legomena_ratio,
            "hapax_dislegomena_ratio": self.hapax_dislegomena_ratio,
            "unique_word_count": self.unique_word_count,
            "total_word_count": self.total_word_count,
            "content_word_count": self.content_word_count,
            "function_word_count": self.function_word_count,
            "most_repeated_words": self.most_repeated_words,
        }


def calculate_lexical_metrics(
    words: List[str],
    content_words: List[str],
    function_words: List[str],
    top_n_repeated: int = 10
) -> LexicalMetrics:
    """Calculate comprehensive lexical metrics."""
    total_words = len(words)
    unique_words = len(set(words))

    if total_words == 0:
        return LexicalMetrics(
            type_token_ratio=None,
            root_ttr=None,
            corrected_ttr=None,
            bilogarithmic_ttr=None,
            herdan_c=None,
            summer_index=None,
            lexical_density=None,
            hapax_legomena_ratio=None,
            hapax_dislegomena_ratio=None,
            unique_word_count=0,
            total_word_count=0,
            content_word_count=0,
            function_word_count=0,
            most_repeated_words=[],
        )

    # Basic TTR
    ttr = unique_words / total_words

    # Root TTR (Guiraud's Index)
    root_ttr = unique_words / math.sqrt(total_words) if total_words > 0 else None

    # Corrected TTR (Carroll's)
    corrected_ttr = (unique_words / math.sqrt(2 * total_words)) * 100 if total_words > 0 else None

    # Bilogarithmic TTR (Herdan's C)
    herdan_c = math.log(unique_words) / math.log(total_words) if unique_words > 0 and total_words > 1 else None
    bilogarithmic_ttr = herdan_c

    # Summer's Index
    summer_index = (
        math.log(math.log(unique_words)) / math.log(math.log(total_words))
        if unique_words > 1 and total_words > math.e else None
    )

    # Lexical density
    content_count = len(content_words)
    function_count = len(function_words)
    lexical_density = content_count / total_words if total_words > 0 else None

    # Hapax statistics
    word_counts = Counter(words)
    hapax_legomena = sum(1 for count in word_counts.values() if count == 1)
    hapax_dislegomena = sum(1 for count in word_counts.values() if count == 2)

    hapax_legomena_ratio = hapax_legomena / unique_words if unique_words > 0 else None
    hapax_dislegomena_ratio = hapax_dislegomena / unique_words if unique_words > 0 else None

    # Most repeated words
    most_repeated = [
        {"word": word, "count": count}
        for word, count in word_counts.most_common(top_n_repeated)
        if count > 1
    ]

    return LexicalMetrics(
        type_token_ratio=round(ttr, 4),
        root_ttr=round(root_ttr, 4) if root_ttr else None,
        corrected_ttr=round(corrected_ttr, 4) if corrected_ttr else None,
        bilogarithmic_ttr=round(bilogarithmic_ttr, 4) if bilogarithmic_ttr else None,
        herdan_c=round(herdan_c, 4) if herdan_c else None,
        summer_index=round(summer_index, 4) if summer_index else None,
        lexical_density=round(lexical_density, 4) if lexical_density else None,
        hapax_legomena_ratio=round(hapax_legomena_ratio, 4) if hapax_legomena_ratio else None,
        hapax_dislegomena_ratio=round(hapax_dislegomena_ratio, 4) if hapax_dislegomena_ratio else None,
        unique_word_count=unique_words,
        total_word_count=total_words,
        content_word_count=content_count,
        function_word_count=function_count,
        most_repeated_words=most_repeated,
    )