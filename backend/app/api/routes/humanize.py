import uuid
import logging
from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import HumanizeRequest, HumanizeResponse
from app.models.enums import HumanizationStyle, HumanizationStrength
from app.services.pipeline import get_pipeline
from app.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["humanize"])


@router.post("/humanize", response_model=HumanizeResponse)
async def humanize_text(request: Request, body: HumanizeRequest):
    """Humanize/naturalize text using local LLM."""
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

    try:
        pipeline = get_pipeline()
        response = pipeline.humanize(body.text, body.style, body.strength, request_id)

        # Override request_id from pipeline with the one from header
        response.request_id = request_id

        # Log request (without user text if privacy enabled)
        if not settings.store_user_text:
            logger.info(f"Request {request_id}: humanized text ({len(body.text)} chars, style={body.style}, strength={body.strength})")
        else:
            logger.info(f"Request {request_id}: humanized text: {body.text[:100]}...")

        return response

    except Exception as e:
        logger.error(f"Request {request_id}: humanization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Humanization failed: {str(e)}")