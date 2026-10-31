import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from app.config import get_settings


_WORD_RE = re.compile(r"[a-zA-Z']+")

# Function words that carry little topical meaning on their own.
_COHERENCE_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "that", "this",
    "these", "those", "is", "are", "was", "were", "be", "been", "being", "of",
    "to", "in", "on", "for", "with", "as", "by", "at", "from", "it", "its",
    "he", "she", "they", "we", "you", "i", "his", "her", "their", "our", "your",
    "not", "no", "do", "does", "did", "have", "has", "had", "will", "would",
    "can", "could", "should", "may", "might", "must", "such", "into", "over",
    "under", "about", "also", "more", "most", "some", "any", "all", "each",
    "who", "whom", "which", "what", "when", "where", "how", "there", "here",
}


def _content_word_set(sentence: str) -> set:
    """Extract lowercase content-word set for a sentence."""
    words = _WORD_RE.findall(sentence.lower())
    return {w for w in words if len(w) > 2 and w not in _COHERENCE_STOPWORDS}


def compute_semantic_coherence(text: str) -> float:
    """
    Compute intra-text semantic coherence on a 0-100 scale.

    Treats each sentence as a bag of terms and measures the mean cosine
    similarity between adjacent sentences using TF weighting. This rewards
    topical continuity (neighbouring sentences discussing the same subject)
    without depending on literal word repetition, which a plain set-overlap
    score would wrongly reward.

    Deterministic and computed purely from the text - no model, no LLM.
    """
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    if len(sentences) < 2:
        return 50.0  # not enough context to judge continuity

    # Build a term x sentence count matrix.
    all_terms = set()
    per_sentence = []
    for sent in sentences:
        terms = [w for w in _WORD_RE.findall(sent.lower())
                 if len(w) > 2 and w not in _COHERENCE_STOPWORDS]
        per_sentence.append(terms)
        all_terms.update(terms)

    if not all_terms:
        return 50.0

    index = {t: i for i, t in enumerate(sorted(all_terms))}
    vectors = []
    for terms in per_sentence:
        vec = [0.0] * len(index)
        for t in terms:
            vec[index[t]] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        vectors.append(vec)

    sims = []
    for a, b in zip(vectors, vectors[1:]):
        sims.append(sum(x * y for x, y in zip(a, b)))

    if not sims:
        return 50.0

    mean_sim = sum(sims) / len(sims)
    # Adjacent-sentence cosine for coherent prose typically lands 0.05-0.40.
    # Map 0.0 -> 0 and 0.40 -> 100, clamped to the valid range.
    return max(0.0, min(mean_sim / 0.40 * 100.0, 100.0))


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


def calculate_naturalness_score(analysis, text: Optional[str] = None) -> NaturalnessScore:
    """Calculate naturalness score from analysis results.

    Args:
        analysis: AnalysisResult with precomputed linguistic metrics.
        text: Raw text the analysis was computed from. Required for the
            semantic_coherence component; if omitted that component falls
            back to a neutral 50.0.
    """
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

    # 4. Template phrase density (inverse).
    # Density is measured per 1000 words: natural prose typically sits near 0-15,
    # heavily templated text can exceed 100. Linear decay so density 0 scores
    # 100 and density 50+ scores 0.
    template_density = analysis.template_phrases.template_phrase_density
    template_score = max(100 - template_density * 2, 0)
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

    # 7. Semantic coherence: topical continuity between adjacent sentences
    # (computed from the text itself, not hard-coded)
    components["semantic_coherence"] = (
        compute_semantic_coherence(text) if text else 50.0
    )

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