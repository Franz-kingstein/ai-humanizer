from dataclasses import dataclass
from typing import List, Optional
import spacy
from spacy.tokens import Doc, Token


@dataclass
class PassiveVoiceMetrics:
    """Passive voice analysis results."""
    passive_sentences: int
    total_sentences: int
    passive_ratio: float
    passive_examples: List[str]
    note: str

    def to_dict(self) -> dict:
        return {
            "passive_sentences": self.passive_sentences,
            "total_sentences": self.total_sentences,
            "passive_ratio": self.passive_ratio,
            "passive_examples": self.passive_examples,
            "note": self.note,
        }


# Note on limitations
PASSIVE_VOICE_NOTE = (
    "Passive voice detection uses spaCy's dependency parsing and morphological features. "
    "This is an ESTIMATE with known limitations:\n"
    "1. May miss passives without 'by' phrases (short passives)\n"
    "2. May misclassify adjectival passives (e.g., 'The door is closed')\n"
    "3. Does not detect get-passives (e.g., 'The window got broken')\n"
    "4. Accuracy varies by domain and sentence complexity\n"
    "5. Results should be interpreted as approximate indicators only"
)


def is_passive_verb(token: Token) -> bool:
    """Check if a verb token is in passive voice."""
    # Check for auxiliary passive (aux:pass)
    for child in token.children:
        if child.dep_ == "auxpass":
            return True

    # Check for nsubjpass (nominal subject of passive)
    for child in token.children:
        if child.dep_ == "nsubjpass":
            return True

    # Check morphological features for passive
    if token.morph.get("Voice") == ["Pass"]:
        return True

    # Check for 'be' + past participle pattern
    if token.tag_ in ("VBN", "VBD") and token.lemma_ == "be":
        # This is an auxiliary, check if head is past participle
        pass

    return False


def analyze_passive_voice(doc: Doc) -> PassiveVoiceMetrics:
    """Analyze passive voice in document."""
    sentences = list(doc.sents)
    total_sentences = len(sentences)

    if total_sentences == 0:
        return PassiveVoiceMetrics(
            passive_sentences=0,
            total_sentences=0,
            passive_ratio=0.0,
            passive_examples=[],
            note=PASSIVE_VOICE_NOTE,
        )

    passive_sentences = 0
    passive_examples = []

    for sent in sentences:
        sent_text = sent.text.strip()
        is_passive = False

        for token in sent:
            if token.pos_ == "VERB" and is_passive_verb(token):
                is_passive = True
                break

        if is_passive:
            passive_sentences += 1
            if len(passive_examples) < 5:  # Limit examples
                passive_examples.append(sent_text)

    passive_ratio = round(passive_sentences / total_sentences, 4) if total_sentences > 0 else 0.0

    return PassiveVoiceMetrics(
        passive_sentences=passive_sentences,
        total_sentences=total_sentences,
        passive_ratio=passive_ratio,
        passive_examples=passive_examples,
        note=PASSIVE_VOICE_NOTE,
    )