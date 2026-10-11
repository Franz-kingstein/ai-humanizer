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

    try:
        return ReadabilityMetrics(
            flesch_reading_ease=round(textstat.flesch_reading_ease(text), 2),
            flesch_kincaid_grade=round(textstat.flesch_kincaid_grade(text), 2),
            gunning_fog=round(textstat.gunning_fog(text), 2),
            smog_index=round(textstat.smog_index(text), 2),
            automated_readability_index=round(textstat.automated_readability_index(text), 2),
            coleman_liau_index=round(textstat.coleman_liau_index(text), 2),
            lix=round(textstat.lix(text), 2),
            rix=round(textstat.rix(text), 2),
            dale_chall_readability_score=round(textstat.dale_chall_readability_score(text), 2),
        )
    except Exception:
        # Fallback to basic metrics if textstat fails
        try:
            return ReadabilityMetrics(
                flesch_reading_ease=round(textstat.flesch_reading_ease(text), 2),
                flesch_kincaid_grade=round(textstat.flesch_kincaid_grade(text), 2),
                gunning_fog=None,
                smog_index=None,
                automated_readability_index=None,
                coleman_liau_index=None,
                lix=None,
                rix=None,
                dale_chall_readability_score=None,
            )
        except Exception:
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