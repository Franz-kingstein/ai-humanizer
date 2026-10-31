import re
import textstat
from dataclasses import dataclass
from typing import Optional


@dataclass
class ReadabilityMetrics:
    """Readability metrics results."""
    flesch_reading_ease: Optional[float]
    flesch_kincaid_grade: Optional[float]
    gunning_fog: Optional[float]
    smog_index: Optional[float]
    automated_readability_index: Optional[float]
    coleman_liau_index: Optional[float]
    lix: Optional[float]
    rix: Optional[float]
    dale_chall_readability_score: Optional[float]

    def to_dict(self) -> dict:
        return {
            "flesch_reading_ease": self.flesch_reading_ease,
            "flesch_kincaid_grade": self.flesch_kincaid_grade,
            "gunning_fog": self.gunning_fog,
            "smog_index": self.smog_index,
            "automated_readability_index": self.automated_readability_index,
            "coleman_liau_index": self.coleman_liau_index,
            "lix": self.lix,
            "rix": self.rix,
            "dale_chall_readability_score": self.dale_chall_readability_score,
        }


def _safe(fn, text):
    """Evaluate one textstat metric, returning None on failure.

    textstat raises KeyError for tokens it cannot look up (e.g. '947' from
    '94.7%'). Each metric is evaluated independently so one unsupported
    token cannot nullify every readability score.
    """
    try:
        return round(float(fn(text)), 2)
    except Exception:
        return None


def calculate_readability(text: str) -> ReadabilityMetrics:
    """Calculate comprehensive readability metrics."""
    if not text or not text.strip():
        return ReadabilityMetrics(
            flesch_reading_ease=None,
            flesch_kincaid_grade=None,
            gunning_fog=None,
            smog_index=None,
            automated_readability_index=None,
            coleman_liau_index=None,
            lix=None,
            rix=None,
            dale_chall_readability_score=None,
        )

    # First try the text as-is.
    metrics = ReadabilityMetrics(
        flesch_reading_ease=_safe(textstat.flesch_reading_ease, text),
        flesch_kincaid_grade=_safe(textstat.flesch_kincaid_grade, text),
        gunning_fog=_safe(textstat.gunning_fog, text),
        smog_index=_safe(textstat.smog_index, text),
        automated_readability_index=_safe(textstat.automated_readability_index, text),
        coleman_liau_index=_safe(textstat.coleman_liau_index, text),
        lix=_safe(textstat.lix, text),
        rix=_safe(textstat.rix, text),
        dale_chall_readability_score=_safe(textstat.dale_chall_readability_score, text),
    )

    # Syllable-based formulas (Flesch, FK, Fog, SMOG, Dale-Chall) fail when a
    # token is missing from the CMU pronouncing dictionary. That happens for
    # numbers ('94.7%' -> '947'), URLs and bare domains ('example.com' ->
    # 'examplecom') and hyphenated compounds ('fast-changing' ->
    # 'fastchanging'). Neutralize those constructs *whole* before handing the
    # text over, because replacing their fragments only creates new unknown
    # tokens such as 'twotwo'.
    if metrics.flesch_reading_ease is None:
        fallback_text = re.sub(r"https?://\S+|www\.\S+|[\w-]+(?:\.[\w-]+)+", "two", text)
        fallback_text = re.sub(r"\d[\d,./]*%?", "two", fallback_text)
        fallback_text = re.sub(r"(?<=[A-Za-z])-(?=[A-Za-z])", " ", fallback_text)

        def _clean(m: "re.Match") -> str:
            token = m.group(0)
            return token if token.replace("'", "").isalpha() else "two"

        fallback_text = re.sub(r"\S+", _clean, fallback_text)
        metrics = ReadabilityMetrics(
            flesch_reading_ease=_safe(textstat.flesch_reading_ease, fallback_text),
            flesch_kincaid_grade=_safe(textstat.flesch_kincaid_grade, fallback_text),
            gunning_fog=_safe(textstat.gunning_fog, fallback_text),
            smog_index=_safe(textstat.smog_index, fallback_text),
            automated_readability_index=metrics.automated_readability_index,
            coleman_liau_index=metrics.coleman_liau_index,
            lix=metrics.lix,
            rix=metrics.rix,
            dale_chall_readability_score=_safe(
                textstat.dale_chall_readability_score, fallback_text
            ),
        )

    return metrics


def get_readability_interpretation(flesch_score: Optional[float]) -> str:
    """Interpret Flesch Reading Ease score."""
    if flesch_score is None:
        return "Unknown"
    if flesch_score >= 90:
        return "Very Easy"
    elif flesch_score >= 80:
        return "Easy"
    elif flesch_score >= 70:
        return "Fairly Easy"
    elif flesch_score >= 60:
        return "Standard"
    elif flesch_score >= 50:
        return "Fairly Difficult"
    elif flesch_score >= 30:
        return "Difficult"
    else:
        return "Very Difficult"