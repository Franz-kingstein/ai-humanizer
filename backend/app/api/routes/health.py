import logging
import torch
from fastapi import APIRouter, Request
from app.models.schemas import HealthResponse
from app.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint."""
    settings = get_settings()

    gpu_available = torch.cuda.is_available()
    gpu_memory_used = None
    gpu_memory_total = None

    if gpu_available:
        gpu_memory_used = torch.cuda.memory_allocated() // (1024 * 1024)
        gpu_memory_total = torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)

    # Check if model is loaded (lazy loading, so check pipeline)
    model_loaded = False
    try:
        from app.services.pipeline import get_pipeline
        pipeline = get_pipeline()
        model_loaded = pipeline.humanizer.is_available()
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        model_loaded=model_loaded,
        device=settings.model_device,
        gpu_available=gpu_available,
        gpu_memory_used_mb=gpu_memory_used,
        gpu_memory_total_mb=gpu_memory_total,
    )


@router.get("/model", response_model=HealthResponse)
async def model_health(request: Request):
    """Model-specific health check: reports the loaded model's details."""
    settings = get_settings()

    model_loaded = False
    try:
        from app.services.pipeline import get_pipeline
        pipeline = get_pipeline()
        model_loaded = pipeline.humanizer.is_available()
        info = pipeline.humanizer.get_model_info()
        logger.info(
            "Model health check: %s on %s (loaded=%s)",
            info.get("name"), info.get("device"), info.get("loaded"),
        )
    except Exception as e:
        logger.error(f"Model health check failed: {e}")

    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        version=settings.app_version,
        model_loaded=model_loaded,
        device=settings.model_device,
        gpu_available=torch.cuda.is_available(),
        gpu_memory_used_mb=None,
        gpu_memory_total_mb=None,
    )