import logging
from typing import Optional
from sentence_transformers import SentenceTransformer
import torch
import numpy as np

from app.config import get_settings


logger = logging.getLogger(__name__)


class SemanticValidator:
    """Validates semantic similarity between original and rewritten text."""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.model: Optional[SentenceTransformer] = None
        self._device = self._get_device()

    def _get_device(self) -> str:
        """Determine device for semantic model."""
        if self.settings.model_device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return self.settings.model_device

    def load_model(self):
        """Load the sentence transformer model."""
        if self.model is None:
            logger.info(f"Loading semantic model: {self.settings.semantic_model_name} on {self._device}")
            self.model = SentenceTransformer(self.settings.semantic_model_name, device=self._device)
            logger.info("Semantic model loaded successfully")

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        if not text1.strip() or not text2.strip():
            return 0.0

        if self.model is None:
            self.load_model()

        # Encode sentences
        embeddings = self.model.encode([text1, text2], convert_to_tensor=True, normalize_embeddings=True)

        # Compute cosine similarity
        similarity = torch.nn.functional.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
        return float(similarity.item())

    def validate(self, original: str, rewritten: str) -> tuple:
        """
        Validate semantic similarity.

        Returns:
            tuple: (similarity_score, is_valid, warning_message)
        """
        similarity = self.compute_similarity(original, rewritten)
        threshold = self.settings.semantic_similarity_threshold
        is_valid = similarity >= threshold

        warning = None
        if not is_valid:
            warning = (
                f"Semantic similarity ({similarity:.3f}) below threshold ({threshold}). "
                f"Meaning may not be fully preserved."
            )
            logger.warning(warning)

        return similarity, is_valid, warning


def get_semantic_validator(settings=None) -> SemanticValidator:
    """Factory function to get semantic validator."""
    return SemanticValidator(settings)