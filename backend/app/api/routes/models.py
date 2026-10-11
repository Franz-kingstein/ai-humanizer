from fastapi import APIRouter, HTTPException
from app.models.schemas import ModelsResponse, ModelInfo
from app.services.pipeline import get_pipeline
from app.config import get_settings


router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """List available models."""
    settings = get_settings()

    try:
        pipeline = get_pipeline()
        current_info = pipeline.humanizer.get_model_info()

        current = ModelInfo(
            name=current_info.get("name", settings.humanizer_model_name),
            provider=current_info.get("provider", settings.model_provider),
            device=current_info.get("device", settings.model_device),
            loaded=current_info.get("loaded", False),
            quantization=current_info.get("quantization"),
        )

        # Available models (for transformers provider)
        available = []
        if settings.model_provider == "transformers":
            # Common small models suitable for RTX 3060 6GB
            candidates = [
                ("Qwen/Qwen2.5-1.5B-Instruct", "transformers", "cuda", "4bit"),
                ("Qwen/Qwen2.5-3B-Instruct", "transformers", "cuda", "4bit"),
                ("microsoft/Phi-3-mini-4k-instruct", "transformers", "cuda", "4bit"),
                ("microsoft/Phi-3.5-mini-instruct", "transformers", "cuda", "4bit"),
                ("google/gemma-2-2b-it", "transformers", "cuda", "4bit"),
                ("meta-llama/Llama-3.2-1B-Instruct", "transformers", "cuda", "4bit"),
                ("meta-llama/Llama-3.2-3B-Instruct", "transformers", "cuda", "4bit"),
            ]
            for name, provider, device, quant in candidates:
                available.append(ModelInfo(
                    name=name,
                    provider=provider,
                    device=device,
                    loaded=(name == current.name),
                    quantization=quant,
                ))

        return ModelsResponse(current=current, available=available)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")