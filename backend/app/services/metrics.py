from dataclasses import dataclass
from typing import Dict, Optional
from app.config import get_settings


@dataclass
class NaturalnessScore:
    """Naturalness/Humanization heuristic score."""
    score: float
    components: Dict[str, float]
    interpretation: str
    disclaimer: str

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 2),
            "components": {k: round(v, 2) for k, v in self.components.items()},
            "interpretation": self.interpretation,
            "disclaimer": self.disclaimer,
        }


DISCLAIMER = (
    "This Naturalness Score is a heuristic research metric based on linguistic features. "
    "It does NOT definitively measure whether text was written by a human or AI. "
    "High scores indicate more varied, diverse, and naturalistic writing patterns. "
    "Low scores suggest more repetitive, formulaic, or template-like patterns. "
    "Results should be interpreted cautiously and in context."
)


def calculate_naturalness_score(analysis) -> NaturalnessScore:
    """Calculate naturalness score from analysis results."""
    settings = get_settings()
    weights = settings.naturalness_weights

    # Extract component scores (0-100 scale)
    components = {}

    # 1. Sentence variation (coefficient of variation)
    cv = analysis.sentence_stats.coefficient_of_variation
    # Normalize: CV of 0.5-1.0 is good, higher is more varied
    sentence_var_score = min(cv * 100, 100) if cv else 0
    components["sentence_variation"] = sentence_var_score

    # 2. Lexical diversity (Type-Token Ratio)
    ttr = analysis.lexical_metrics.type_token_ratio
    # TTR of 0.4-0.6 is typical for natural text
    lexical_div_score = min(ttr * 200, 100) if ttr else 0
    components["lexical_diversity"] = lexical_div_score

    # 3. Repetition (inverse of repetition ratio)
    bigram_rep = analysis.ngram_repetition.bigram_repetition_ratio
    trigram_rep = analysis.ngram_repetition.trigram_repetition_ratio
    avg_rep = (bigram_rep + trigram_rep) / 2
    # Lower repetition is better
    repetition_score = max(100 - avg_rep * 200, 0)
    components["repetition"] = repetition_score

    # 4. Template phrase density (inverse)
    template_density = analysis.template_phrases.template_phrase_density
    # Lower density is better (per 1000 words)
    template_score = max(100 - template_density * 10, 0)
    components["template_density"] = template_score

    # 5. Passive voice (inverse - less passive is generally more natural)
    passive_ratio = analysis.passive_voice.passive_ratio
    passive_score = max(100 - passive_ratio * 200, 0)
    components["passive_voice"] = passive_score

    # 6. Readability (Flesch Reading Ease - closer to 60-70 is ideal)
    flesch = analysis.readability.flesch_reading_ease
    if flesch is not None:
        # Optimal range 60-70, penalize too high or too low
        if 60 <= flesch <= 70:
            readability_score = 100
        elif flesch > 70:
            readability_score = max(100 - (flesch - 70) * 2, 0)
        else:
            readability_score = max(100 - (60 - flesch) * 3, 0)
    else:
        readability_score = 50
    components["readability"] = readability_score

    # 7. Semantic coherence (placeholder - would need semantic model)
    # For now, use a neutral score
    components["semantic_coherence"] = 70.0

    # Calculate weighted score
    total_score = sum(
        components.get(k, 0) * weights.get(k, 0)
        for k in weights
    )

    # Interpretation
    if total_score >= 80:
        interpretation = "High naturalness - varied, diverse, human-like patterns"
    elif total_score >= 60:
        interpretation = "Moderate naturalness - some formulaic patterns detected"
    elif total_score >= 40:
        interpretation = "Low naturalness - repetitive, template-like patterns"
    else:
        interpretation = "Very low naturalness - highly formulaic or AI-like patterns"

    return NaturalnessScore(
        score=round(total_score, 2),
        components=components,
        interpretation=interpretation,
        disclaimer=DISCLAIMER,
    )