import time
import logging
import httpx
from typing import Dict, Any, Optional

from app.services.humanizer import Humanizer, HumanizationResult, build_humanization_prompt
from app.models.enums import HumanizationStyle, HumanizationStrength
from app.config import get_settings


logger = logging.getLogger(__name__)


class OllamaHumanizer(Humanizer):
    """Ollama-based humanizer."""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._base_url = "http://localhost:11434"
        self._model_name = self.settings.humanizer_model_name
        self._loaded = False
        self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def _close_client(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def is_available(self) -> bool:
        """Check if Ollama is available and model is loaded."""
        try:
            import requests
            response = requests.get(f"{self._base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m["name"].startswith(self._model_name.split(":")[0]) for m in models)
        except Exception:
            pass
        return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "name": self._model_name,
            "provider": "ollama",
            "device": "ollama",
            "loaded": self._loaded,
            "base_url": self._base_url,
        }

    def humanize(
        self,
        text: str,
        style: HumanizationStyle,
        strength: HumanizationStrength,
    ) -> HumanizationResult:
        """Humanize text using Ollama."""
        # For sync version, we use synchronous requests
        import requests

        if not self.is_available():
            raise RuntimeError("Ollama not available or model not loaded")

        start_time = time.time()

        prompt = build_humanization_prompt(text, style, strength)

        from app.services.humanizer import get_strength_params
        params = get_strength_params(strength)

        payload = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": params["temperature"],
                "top_p": params["top_p"],
                "repeat_penalty": params["repetition_penalty"],
                "num_predict": int(self.settings.humanizer_max_new_tokens * params["max_new_tokens_multiplier"]),
            },
        }

        response = requests.post(
            f"{self._base_url}/api/generate",
            json=payload,
            timeout=120,
        )

        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error: {response.text}")

        result = response.json()
        generated_text = result.get("response", "").strip()

        processing_time = (time.time() - start_time) * 1000

        self._loaded = True

        return HumanizationResult(
            text=generated_text,
            model_info=self.get_model_info(),
            processing_time_ms=processing_time,
        )

    async def humanize_async(
        self,
        text: str,
        style: HumanizationStyle,
        strength: HumanizationStrength,
    ) -> HumanizationResult:
        """Humanize text using Ollama (async version)."""
        if not self.is_available():
            raise RuntimeError("Ollama not available or model not loaded")

        start_time = time.time()

        prompt = build_humanization_prompt(text, style, strength)

        from app.services.humanizer import get_strength_params
        params = get_strength_params(strength)

        payload = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": params["temperature"],
                "top_p": params["top_p"],
                "repeat_penalty": params["repetition_penalty"],
                "num_predict": int(self.settings.humanizer_max_new_tokens * params["max_new_tokens_multiplier"]),
            },
        }

        client = self._get_client()
        response = await client.post(f"{self._base_url}/api/generate", json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error: {response.text}")

        result = response.json()
        generated_text = result.get("response", "").strip()

        processing_time = (time.time() - start_time) * 1000

        self._loaded = True

        return HumanizationResult(
            text=generated_text,
            model_info=self.get_model_info(),
            processing_time_ms=processing_time,
        )