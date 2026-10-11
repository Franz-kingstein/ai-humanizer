from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from app.models.enums import HumanizationStyle, HumanizationStrength
from app.config import get_settings


@dataclass
class HumanizationResult:
    """Result of humanization."""
    text: str
    model_info: Dict[str, Any]
    processing_time_ms: float


class Humanizer(ABC):
    """Abstract base class for humanizers."""

    @abstractmethod
    def humanize(
        self,
        text: str,
        style: HumanizationStyle,
        strength: HumanizationStrength,
    ) -> HumanizationResult:
        """Humanize the input text."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the humanizer is available."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        pass


def get_style_prompt(style: HumanizationStyle) -> str:
    """Get style-specific prompt instructions."""
    prompts = {
        HumanizationStyle.NATURAL: (
            "Rewrite the text in a natural, conversational style as if a human wrote it. "
            "Use varied sentence structures, natural transitions, and authentic voice. "
            "Avoid overly formal or robotic phrasing."
        ),
        HumanizationStyle.ACADEMIC: (
            "Rewrite the text in an academic style suitable for scholarly writing. "
            "Use precise terminology, formal tone, and structured argumentation. "
            "Maintain objectivity and clarity."
        ),
        HumanizationStyle.PROFESSIONAL: (
            "Rewrite the text in a professional business style. "
            "Be clear, concise, and polished. Use appropriate business terminology "
            "and maintain a confident, authoritative tone."
        ),
        HumanizationStyle.CASUAL: (
            "Rewrite the text in a casual, friendly style as if writing to a colleague or friend. "
            "Use contractions, simpler vocabulary, and relaxed sentence structures. "
            "Sound approachable and genuine."
        ),
        HumanizationStyle.TECHNICAL: (
            "Rewrite the text in a technical style for a technical audience. "
            "Use precise technical terminology, maintain accuracy, and include relevant details. "
            "Be clear and unambiguous."
        ),
    }
    return prompts.get(style, prompts[HumanizationStyle.NATURAL])


def get_strength_params(strength: HumanizationStrength) -> Dict[str, Any]:
    """Get generation parameters based on strength."""
    params = {
        HumanizationStrength.LOW: {
            "temperature": 0.5,
            "top_p": 0.85,
            "repetition_penalty": 1.05,
            "max_new_tokens_multiplier": 1.0,
        },
        HumanizationStrength.MEDIUM: {
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "max_new_tokens_multiplier": 1.2,
        },
        HumanizationStrength.HIGH: {
            "temperature": 0.85,
            "top_p": 0.95,
            "repetition_penalty": 1.15,
            "max_new_tokens_multiplier": 1.5,
        },
    }
    return params.get(strength, params[HumanizationStrength.MEDIUM])


def build_humanization_prompt(
    text: str,
    style: HumanizationStyle,
    strength: HumanizationStrength,
) -> str:
    """Build the complete humanization prompt."""
    style_instruction = get_style_prompt(style)
    strength_params = get_strength_params(strength)

    # Base prompt with strong content preservation instructions
    prompt = f"""<|im_start|>system
You are an expert text naturalizer. Your task is to rewrite the provided text to sound more natural and human-written while STRICTLY preserving all factual content.

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. PRESERVE ALL FACTS: Numbers, dates, percentages, statistics, measurements, named entities, technical terms, citations, URLs, and proper nouns MUST remain EXACTLY the same.
2. PRESERVE MEANING: The rewritten text must convey the same information and intent as the original.
3. DO NOT ADD INFORMATION: Never add facts, claims, examples, or details not present in the original text.
4. DO NOT REMOVE INFORMATION: Do not omit any factual content from the original.
5. STYLE: {style_instruction}

Strength level: {strength.value.upper()} - {'Minimal changes, light polishing' if strength == HumanizationStrength.LOW else 'Moderate restructuring for natural flow' if strength == HumanizationStrength.MEDIUM else 'Significant restructuring for maximum naturalness'}

Original text:
{text}

Rewritten text (preserving all facts exactly):<|im_end|>
<|im_start|>assistant
"""

    return prompt


def get_humanizer(provider: str = None, settings=None) -> Humanizer:
    """Factory function to get humanizer based on provider."""
    settings = settings or get_settings()
    provider = provider or settings.model_provider

    if provider == "transformers":
        from app.services.humanizer_transformers import TransformersHumanizer
        return TransformersHumanizer(settings)
    elif provider == "ollama":
        from app.services.humanizer_ollama import OllamaHumanizer
        return OllamaHumanizer(settings)
    else:
        raise ValueError(f"Unknown provider: {provider}")