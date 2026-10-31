import time
import logging
import torch
from typing import Dict, Any, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from app.services.humanizer import Humanizer, HumanizationResult, build_humanization_prompt
from app.models.enums import HumanizationStyle, HumanizationStrength
from app.config import get_settings


logger = logging.getLogger(__name__)


class TransformersHumanizer(Humanizer):
    """Local Transformers-based humanizer."""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.model = None
        self.tokenizer = None
        self._device = self._get_device()
        self._loaded = False

    def _get_device(self) -> str:
        """Determine device."""
        if self.settings.model_device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return self.settings.model_device

    def _get_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """Get quantization config based on settings."""
        if self.settings.humanizer_quantization == "4bit":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
        elif self.settings.humanizer_quantization == "8bit":
            return BitsAndBytesConfig(load_in_8bit=True)
        return None

    def _resolve_torch_dtype(self):
        """Resolve model dtype from settings.

        "auto" picks float16 on CUDA and bfloat16 on CPU. bfloat16 keeps the
        same exponent range as float32, so it is numerically safe for LLM
        inference while halving the model's resident memory.
        """
        requested = (self.settings.humanizer_torch_dtype or "auto").lower()

        if requested == "auto":
            requested = "float16" if self._device == "cuda" else "bfloat16"

        dtype_map = {
            "float32": torch.float32,
            "fp32": torch.float32,
            "float16": torch.float16,
            "fp16": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
        }
        dtype = dtype_map.get(requested)
        if dtype is None:
            logger.warning(f"Unknown torch dtype '{requested}', using float32")
            return torch.float32

        if dtype == torch.bfloat16 and self._device == "cpu":
            try:
                # Verify the CPU can actually run bfloat16 ops before loading.
                torch.zeros(1, dtype=torch.bfloat16).sum()
            except Exception as e:
                logger.warning(f"bfloat16 unsupported on this CPU ({e}); using float32")
                return torch.float32

        logger.info(f"Model dtype: {requested} on {self._device}")
        return dtype

    def load_model(self):
        """Load model and tokenizer."""
        if self._loaded:
            return

        logger.info(f"Loading model: {self.settings.humanizer_model_name} on {self._device}")

        quantization_config = self._get_quantization_config()

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.settings.humanizer_model_name,
            revision=self.settings.humanizer_model_revision,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        model_kwargs = {
            "revision": self.settings.humanizer_model_revision,
            "trust_remote_code": True,
            "torch_dtype": self._resolve_torch_dtype(),
        }

        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
            # Only use device_map="auto" for CUDA; for CPU, disable quantization or use device_map="cpu"
            if self._device == "cuda":
                model_kwargs["device_map"] = "auto"
            else:
                # For CPU, don't use quantization with device_map
                model_kwargs["device_map"] = "cpu"
                model_kwargs.pop("quantization_config", None)
                logger.info("Quantization disabled for CPU device")
        else:
            model_kwargs["device_map"] = self._device

        self.model = AutoModelForCausalLM.from_pretrained(
            self.settings.humanizer_model_name,
            **model_kwargs
        )

        self.model.eval()
        self._loaded = True
        logger.info("Model loaded successfully")

    def is_available(self) -> bool:
        """Check if humanizer is available."""
        try:
            if not self._loaded:
                self.load_model()
            return self.model is not None
        except Exception as e:
            logger.error(f"Humanizer not available: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        info = {
            "name": self.settings.humanizer_model_name,
            "provider": "transformers",
            "device": self._device,
            "loaded": self._loaded,
            "quantization": self.settings.humanizer_quantization,
        }

        if self._loaded and torch.cuda.is_available():
            info["gpu_memory_used_mb"] = torch.cuda.memory_allocated() // (1024 * 1024)
            info["gpu_memory_total_mb"] = torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)

        return info

    def humanize(
        self,
        text: str,
        style: HumanizationStyle,
        strength: HumanizationStrength,
    ) -> HumanizationResult:
        """Humanize text using local transformers model."""
        if not self._loaded:
            self.load_model()

        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        # Get actual model device (handles device_map="auto" case)
        model_device = next(self.model.parameters()).device

        # Build prompt
        prompt = build_humanization_prompt(text, style, strength)

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
        inputs = {k: v.to(model_device) for k, v in inputs.items()}

        # Get strength params
        from app.services.humanizer import get_strength_params
        params = get_strength_params(strength)

        max_new_tokens = int(self.settings.humanizer_max_new_tokens * params["max_new_tokens_multiplier"])

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=params["temperature"],
                top_p=params["top_p"],
                repetition_penalty=params["repetition_penalty"],
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Decode only the new tokens
        input_length = inputs["input_ids"].shape[1]
        new_tokens = outputs[0][input_length:]
        generated_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

        processing_time = (time.time() - start_time) * 1000

        return HumanizationResult(
            text=generated_text.strip(),
            model_info=self.get_model_info(),
            processing_time_ms=processing_time,
        )