import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.routes import health, analyze, humanize, compare, models
from app.utils.logging import setup_logging


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Model provider: {settings.model_provider}")
    logger.info(f"Device: {settings.model_device}")

    # Pre-load spaCy model
    try:
        import spacy
        logger.info(f"Loading spaCy model: {settings.spacy_model}")
        nlp = spacy.load(settings.spacy_model)
        app.state.nlp = nlp
        logger.info("spaCy model loaded")
    except Exception as e:
        logger.warning(f"Could not load spaCy model: {e}")
        app.state.nlp = None

    # Pre-load semantic model
    try:
        from app.services.semantic_validator import get_semantic_validator
        validator = get_semantic_validator()
        validator.load_model()
        logger.info("Semantic model loaded")
    except Exception as e:
        logger.warning(f"Could not load semantic model: {e}")

    # Pre-load humanizer model if transformers.
    # Use the pipeline singleton so the SAME instance is reused by requests;
    # creating a separate humanizer here would load the weights twice.
    if settings.model_provider == "transformers":
        try:
            from app.services.pipeline import get_pipeline
            pipeline = get_pipeline()
            pipeline.humanizer.load_model()
            logger.info("Humanizer model loaded")
        except Exception as e:
            logger.warning(f"Could not load humanizer model: {e}")

    yield

    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Humanizer / NLP Naturalization and Writing-Pattern Analysis System",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get(settings.request_id_header)
    if not request_id:
        import uuid
        request_id = str(uuid.uuid4())[:8]

    response = await call_next(request)
    response.headers[settings.request_id_header] = request_id
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(humanize.router)
app.include_router(compare.router)
app.include_router(models.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI Humanizer / NLP Naturalization System",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )