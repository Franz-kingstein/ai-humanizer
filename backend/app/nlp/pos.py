from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional
import spacy
from spacy.tokens import Doc


@dataclass
class POSDistribution:
    """Part-of-speech distribution results."""
    counts: Dict[str, int]
    percentages: Dict[str, float]
    total_tokens: int

    def to_dict(self) -> dict:
        return {
            "counts": self.counts,
            "percentages": self.percentages,
            "total_tokens": self.total_tokens,
        }


@dataclass
class PunctuationDistribution:
    """Punctuation distribution results."""
    counts: Dict[str, int]
    percentages: Dict[str, float]
    total_punctuation: int

    def to_dict(self) -> dict:
        return {
            "counts": self.counts,
            "percentages": self.percentages,
            "total_punctuation": self.total_punctuation,
        }


@dataclass
class ConjunctionIndicators:
    """Conjunction and connector indicators."""
    coordinating: int
    subordinating: int
    correlative: int
    conjunctive_adverbs: int
    total: int

    def to_dict(self) -> dict:
        return {
            "coordinating": self.coordinating,
            "subordinating": self.subordinating,
            "correlative": self.correlative,
            "conjunctive_adverbs": self.conjunctive_adverbs,
            "total": self.total,
        }


# POS tag categories
CONTENT_POS = {"NOUN", "VERB", "ADJ", "ADV", "PROPN"}
FUNCTION_POS = {"ADP", "AUX", "CCONJ", "DET", "PART", "PRON", "SCONJ"}
PUNCTUATION_POS = {"PUNCT", "SYM"}

# Conjunction lists
COORDINATING = {"and", "but", "or", "nor", "for", "so", "yet"}
SUBORDINATING = {
    "because", "since", "as", "although", "though", "even though",
    "while", "whereas", "if", "unless", "until", "when", "whenever",
    "where", "wherever", "after", "before", "once", "since"
}
CORRELATIVE = {
    "both and", "either or", "neither nor", "not only but also",
    "whether or", "as as", "so as", "such that"
}
CONJUNCTIVE_ADVERBS = {
    "however", "therefore", "moreover", "furthermore", "additionally",
    "consequently", "nevertheless", "nonetheless", "meanwhile",
    "subsequently", "accordingly", "hence", "thus", "otherwise",
    "instead", "likewise", "similarly", "indeed", "in fact"
}


def analyze_pos(doc: Doc) -> POSDistribution:
    """Analyze part-of-speech distribution."""
    pos_counts = Counter(token.pos_ for token in doc if not token.is_space)
    total = sum(pos_counts.values())

    percentages = {}
    if total > 0:
        percentages = {pos: round(count / total * 100, 2) for pos, count in pos_counts.items()}

    return POSDistribution(
        counts=dict(pos_counts),
        percentages=percentages,
        total_tokens=total,
    )


def analyze_punctuation(doc: Doc) -> PunctuationDistribution:
    """Analyze punctuation distribution."""
    punct_counts = Counter(token.text for token in doc if token.pos_ == "PUNCT")
    total = sum(punct_counts.values())

    percentages = {}
    if total > 0:
        percentages = {p: round(count / total * 100, 2) for p, count in punct_counts.items()}

    return PunctuationDistribution(
        counts=dict(punct_counts),
        percentages=percentages,
        total_punctuation=total,
    )


def analyze_conjunctions(doc: Doc) -> ConjunctionIndicators:
    """Analyze conjunction usage."""
    text_lower = doc.text.lower()
    words = [token.text.lower() for token in doc]

    coordinating = sum(1 for w in words if w in COORDINATING)
    subordinating = sum(1 for w in words if w in SUBORDINATING)
    conjunctive_adverbs = sum(1 for w in words if w in CONJUNCTIVE_ADVERBS)

    # Correlative conjunctions (simple check)
    correlative = 0
    for corr in CORRELATIVE:
        if corr in text_lower:
            correlative += 1

    total = coordinating + subordinating + correlative + conjunctive_adverbs

    return ConjunctionIndicators(
        coordinating=coordinating,
        subordinating=subordinating,
        correlative=correlative,
        conjunctive_adverbs=conjunctive_adverbs,
        total=total,
    )


def get_syntax_features(doc: Doc) -> dict:
    """Extract syntactic features from dependency parse."""
    dep_counts = Counter(token.dep_ for token in doc if not token.is_space)
    total = sum(dep_counts.values())

    # Key syntactic indicators
    features = {
        "dependency_distribution": {
            dep: round(count / total * 100, 2) if total > 0 else 0
            for dep, count in dep_counts.items()
        },
        "nsubj_count": dep_counts.get("nsubj", 0),
        "dobj_count": dep_counts.get("dobj", 0),
        "prep_count": dep_counts.get("prep", 0),
        "advcl_count": dep_counts.get("advcl", 0),
        "relcl_count": dep_counts.get("relcl", 0),
        "ccomp_count": dep_counts.get("ccomp", 0),
        "xcomp_count": dep_counts.get("xcomp", 0),
    }

    return features