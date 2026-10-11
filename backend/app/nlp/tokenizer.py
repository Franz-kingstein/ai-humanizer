import re
from typing import List, Optional
import spacy
from spacy.tokens import Doc


class TextTokenizer:
    """Configurable text tokenizer using spaCy."""

    def __init__(self, nlp: spacy.Language, use_stopwords: bool = True):
        self.nlp = nlp
        self.use_stopwords = use_stopwords

    def tokenize(self, text: str) -> Doc:
        """Tokenize text with spaCy."""
        return self.nlp(text)

    def get_words(self, doc: Doc, lowercase: bool = True, alpha_only: bool = True) -> List[str]:
        """Extract words from doc with optional filtering."""
        words = []
        for token in doc:
            if alpha_only and not token.is_alpha:
                continue
            if not self.use_stopwords and token.is_stop:
                continue
            word = token.text.lower() if lowercase else token.text
            words.append(word)
        return words

    def get_sentences(self, doc: Doc) -> List[str]:
        """Extract sentences from doc."""
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    def get_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        return paragraphs


# Sentence splitting patterns for fallback
SENTENCE_ENDINGS = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def simple_sentence_split(text: str) -> List[str]:
    """Simple sentence splitter without spaCy."""
    sentences = SENTENCE_ENDINGS.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def simple_word_tokenize(text: str, lowercase: bool = True) -> List[str]:
    """Simple word tokenizer without spaCy."""
    words = re.findall(r"\b[a-zA-Z']+\b", text)
    if lowercase:
        words = [w.lower() for w in words]
    return words


def get_tokenizer(nlp: Optional[spacy.Language] = None, use_stopwords: bool = True) -> TextTokenizer:
    """Factory function to get tokenizer."""
    if nlp is None:
        nlp = spacy.blank("en")
    return TextTokenizer(nlp, use_stopwords)


from dataclasses import dataclass
from typing import List, Optional
import statistics


@dataclass
class SentenceStatistics:
    """Sentence length statistics."""
    sentence_count: int
    min_length: int
    max_length: int
    mean_length: float
    median_length: float
    std_dev: float
    coefficient_of_variation: float
    lengths: List[int]

    def to_dict(self) -> dict:
        return {
            "sentence_count": self.sentence_count,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "mean_length": round(self.mean_length, 2),
            "median_length": round(self.median_length, 2),
            "std_dev": round(self.std_dev, 2),
            "coefficient_of_variation": round(self.coefficient_of_variation, 4),
            "lengths": self.lengths,
        }


@dataclass
class BasicStatistics:
    """Basic text statistics."""
    character_count: int
    character_count_no_spaces: int
    word_count: int
    unique_word_count: int
    sentence_count: int
    paragraph_count: int
    avg_word_length: float
    avg_sentence_length: float

    def to_dict(self) -> dict:
        return {
            "character_count": self.character_count,
            "character_count_no_spaces": self.character_count_no_spaces,
            "word_count": self.word_count,
            "unique_word_count": self.unique_word_count,
            "sentence_count": self.sentence_count,
            "paragraph_count": self.paragraph_count,
            "avg_word_length": round(self.avg_word_length, 2),
            "avg_sentence_length": round(self.avg_sentence_length, 2),
        }


def calculate_basic_stats(
    text: str,
    words: List[str],
    sentences: List[str],
    paragraphs: List[str],
    unique_words: int
) -> BasicStatistics:
    """Calculate basic text statistics."""
    char_count = len(text)
    char_count_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    word_count = len(words)
    sentence_count = len(sentences)
    paragraph_count = len(paragraphs)

    avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0.0
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0.0

    return BasicStatistics(
        character_count=char_count,
        character_count_no_spaces=char_count_no_spaces,
        word_count=word_count,
        unique_word_count=unique_words,
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        avg_word_length=avg_word_length,
        avg_sentence_length=avg_sentence_length,
    )


def calculate_sentence_stats(sentences: List[str], words_per_sentence: List[int]) -> SentenceStatistics:
    """Calculate sentence length statistics."""
    sent_count = len(sentences)

    if sent_count == 0:
        return SentenceStatistics(
            sentence_count=0,
            min_length=0,
            max_length=0,
            mean_length=0.0,
            median_length=0.0,
            std_dev=0.0,
            coefficient_of_variation=0.0,
            lengths=[],
        )

    lengths = words_per_sentence
    min_len = min(lengths)
    max_len = max(lengths)
    mean_len = statistics.mean(lengths)
    median_len = statistics.median(lengths)
    std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0.0
    cv = std_dev / mean_len if mean_len > 0 else 0.0

    return SentenceStatistics(
        sentence_count=sent_count,
        min_length=min_len,
        max_length=max_len,
        mean_length=mean_len,
        median_length=median_len,
        std_dev=std_dev,
        coefficient_of_variation=cv,
        lengths=lengths,
    )