import time
import uuid
import logging
from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, NaturalnessScore, Warning
from app.services.pipeline import get_pipeline
from app.services.metrics import calculate_naturalness_score
from app.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: Request, body: AnalyzeRequest):
    """Analyze text and return comprehensive linguistic metrics."""
    settings = get_settings()
    request_id = request.headers.get(settings.request_id_header, str(uuid.uuid4())[:8])

    # Validate input length
    if len(body.text) > settings.max_input_characters:
        raise HTTPException(
            status_code=400,
            detail=f"Text exceeds maximum length of {settings.max_input_characters} characters"
        )

    word_count = len(body.text.split())
    if word_count > settings.max_input_words:
        raise HTTPException(
            status_code=400,
            detail=f"Text exceeds maximum word count of {settings.max_input_words}"
        )

    start_time = time.time()

    try:
        pipeline = get_pipeline()
        analysis, naturalness, processing_time, _ = pipeline.analyze(body.text, request_id)

        warnings = []
        # Add any relevant warnings
        if analysis.basic_stats.word_count < 10:
            warnings.append(Warning(
                type="short_text",
                message="Text is very short; metrics may not be reliable",
                severity="info"
            ))

        processing_time = (time.time() - start_time) * 1000

        # Log request (without user text if privacy enabled)
        if not settings.store_user_text:
            logger.info(f"Request {request_id}: analyzed text ({analysis.basic_stats.word_count} words)")
        else:
            logger.info(f"Request {request_id}: analyzed text: {body.text[:100]}...")

        return AnalyzeResponse(
            request_id=request_id,
            analysis=analysis.to_dict(),
            naturalness_score=NaturalnessScore(
                score=naturalness.score,
                components=naturalness.components,
                interpretation=naturalness.interpretation,
                disclaimer=naturalness.disclaimer,
            ),
            warnings=warnings,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"Request {request_id}: analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")