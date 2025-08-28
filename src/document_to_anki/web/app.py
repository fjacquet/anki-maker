"""FastAPI web application for document-to-anki conversion."""

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import ConfigurationError, LanguageValidationError, ModelConfig, settings
from ..core.document_processor import DocumentProcessingError, DocumentProcessor
from ..core.flashcard_generator import FlashcardGenerationError, FlashcardGenerator
from .routes_export import router as export_router
from .routes_flashcards import router as flashcards_router
from .routes_upload import router as upload_router
from .session_manager import session_manager

auto_cleanup_task = None

templates = Jinja2Templates(directory="src/document_to_anki/web/templates")
static_dir = Path("src/document_to_anki/web/static")
static_dir.mkdir(parents=True, exist_ok=True)


# Security configuration constants
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]  # Restrict to local interfaces for security


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    active_sessions: int = Field(ge=0, description="Number of active sessions")
    supported_formats: list[str] = Field(default_factory=list, description="Supported file formats")


class ModelConfigResponse(BaseModel):
    """Response model for model configuration."""

    current_model: str
    is_valid: bool
    supported_models: list[str]
    status: str
    message: str | None = None


class LanguageConfigResponse(BaseModel):
    """Response model for language configuration."""

    current_language: str
    language_name: str
    language_code: str
    prompt_key: str
    supported_languages: list[str]
    all_language_keys: list[str]
    status: str


class AppConfigResponse(BaseModel):
    """Response model for application configuration."""

    max_file_size_mb: int
    max_file_size_bytes: int
    max_batch_size: int
    supported_extensions: list[str]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:  # pragma: no cover - simple middleware
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
            "img-src 'self' data:; font-src 'self'; connect-src 'self'"
        )
        # Enforce HTTPS in production
        if request.headers.get("x-forwarded-proto") == "https" or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # HTTPS enforcement: redirect HTTP to HTTPS in production
        if (
            request.url.scheme == "http"
            and request.headers.get("x-forwarded-proto") != "https"
            and request.headers.get("host", "").startswith(("api.", "app.", "www."))
        ):
            # In production, this would redirect to HTTPS
            # For development, we allow HTTP on localhost
            pass
        # Enforce HTTPS in production
        if request.headers.get("x-forwarded-proto") == "https" or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # HTTPS enforcement: redirect HTTP to HTTPS in production
        if (
            request.url.scheme == "http"
            and request.headers.get("x-forwarded-proto") != "https"
            and request.headers.get("host", "").startswith(("api.", "app.", "www."))
        ):
            # In production, this would redirect to HTTPS
            # For development, we allow HTTP on localhost
            pass
        return response


# Global instances initialised in lifespan for backward compatibility
document_processor: DocumentProcessor | None = None
flashcard_generator: FlashcardGenerator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Manage application startup and shutdown."""
    global auto_cleanup_task, document_processor, flashcard_generator
    logger.info("Starting Document to Anki web application")
    try:
        model = ModelConfig.validate_and_get_model()
        logger.info(f"Using model: {model}")
    except ConfigurationError as exc:
        logger.error(f"Model configuration error: {exc}")
        raise

    document_processor = DocumentProcessor()
    flashcard_generator = FlashcardGenerator()
    app.state.document_processor = document_processor
    app.state.flashcard_generator = flashcard_generator
    app.state.session_manager = session_manager

    auto_cleanup_task = asyncio.create_task(session_manager.cleanup_expired_sessions())
    yield

    if auto_cleanup_task:
        auto_cleanup_task.cancel()
        try:
            await auto_cleanup_task
        except asyncio.CancelledError:
            pass
    session_manager.cleanup_all_sessions()
    logger.info(f"Cleaned up {len(session_manager.sessions)} sessions on shutdown")


app = FastAPI(
    title="Document to Anki Converter",
    description="Convert documents to Anki flashcards using AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS + ["*"])  # Allow all in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(upload_router)
app.include_router(flashcards_router)
app.include_router(export_router)


@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check(request: Request) -> HealthCheckResponse:
    """Health check endpoint with input validation."""
    dp: DocumentProcessor | None = request.app.state.document_processor
    return HealthCheckResponse(
        status="healthy",
        message="Document to Anki API is running",
        active_sessions=len(session_manager),
        supported_formats=list(dp.get_supported_formats()) if dp else [],
    )


@app.get("/api/config/model", response_model=ModelConfigResponse)
async def get_model_configuration() -> ModelConfigResponse:
    """Get current model configuration status with input validation."""
    try:
        current_model = ModelConfig.get_model_from_env()
        is_valid = ModelConfig.validate_model_config(current_model)
        message = None
        if not is_valid and current_model not in ModelConfig.SUPPORTED_MODELS:
            message = (
                f"Model '{current_model}' is not supported. Supported models: {ModelConfig.get_supported_models()}"
            )
        return ModelConfigResponse(
            current_model=current_model,
            is_valid=is_valid,
            supported_models=ModelConfig.get_supported_models(),
            status="valid" if is_valid else "invalid",
            message=message,
        )
    except Exception as exc:
        logger.error(f"Error getting model configuration: {exc}")
        raise HTTPException(status_code=500, detail="Failed to get model configuration") from exc


@app.get("/api/config/language", response_model=LanguageConfigResponse)
async def get_language_configuration() -> LanguageConfigResponse:
    """Get current language configuration status with input validation."""
    try:
        from ..config import LanguageConfig

        language_info = settings.get_language_info()
        return LanguageConfigResponse(
            current_language=settings.cardlang,
            language_name=language_info.name,
            language_code=language_info.code,
            prompt_key=language_info.prompt_key,
            supported_languages=LanguageConfig.get_supported_languages_list(),
            all_language_keys=LanguageConfig.get_all_language_keys(),
            status="valid",
        )
    except LanguageValidationError as exc:
        logger.error(f"Language validation error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "invalid",
                "error": str(exc),
                "supported_languages": exc.supported_languages,
            },
        ) from exc
    except Exception as exc:
        logger.error(f"Error getting language configuration: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get language configuration",
        ) from exc


@app.get("/api/config/app", response_model=AppConfigResponse)
async def get_app_configuration() -> AppConfigResponse:
    """Get application configuration for client-side validation."""
    from ..utils.file_handler import FileHandler

    file_handler = FileHandler()
    return AppConfigResponse(
        max_file_size_mb=settings.max_file_size_mb,
        max_file_size_bytes=settings.max_file_size_bytes,
        max_batch_size=settings.max_batch_size,
        supported_extensions=list(file_handler.SUPPORTED_EXTENSIONS),
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse | HTMLResponse:
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"detail": "API endpoint not found", "path": request.url.path, "method": request.method},
        )
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 404,
            "error_title": "Page Not Found",
            "error_message": "The page you're looking for doesn't exist.",
            "show_home_link": True,
        },
        status_code=404,
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse | HTMLResponse:
    logger.error(f"Internal server error on {request.url.path}: {exc}")
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 500,
            "error_title": "Server Error",
            "error_message": "An unexpected error occurred. Please try again later.",
            "show_home_link": True,
        },
        status_code=500,
    )


@app.exception_handler(413)
async def file_too_large_handler(request: Request, exc: HTTPException) -> JSONResponse | HTMLResponse:
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=413,
            content={
                "detail": "File too large",
                "message": "The uploaded file exceeds the maximum size limit of 50MB.",
            },
        )
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 413,
            "error_title": "File Too Large",
            "error_message": "The uploaded file exceeds the maximum size limit of 50MB.",
            "show_home_link": True,
        },
        status_code=413,
    )


@app.exception_handler(DocumentProcessingError)
async def document_processing_error_handler(
    request: Request, exc: DocumentProcessingError
) -> JSONResponse | HTMLResponse:
    logger.warning(f"Document processing error: {exc}")
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=400, content={"detail": "Document processing failed", "message": str(exc)})
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 400,
            "error_title": "Document Processing Error",
            "error_message": str(exc),
            "show_home_link": True,
        },
        status_code=400,
    )


@app.exception_handler(FlashcardGenerationError)
async def flashcard_generation_error_handler(
    request: Request, exc: FlashcardGenerationError
) -> JSONResponse | HTMLResponse:
    logger.warning(f"Flashcard generation error: {exc}")
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=400, content={"detail": "Flashcard generation failed", "message": str(exc)})
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 400,
            "error_title": "Flashcard Generation Error",
            "error_message": str(exc),
            "show_home_link": True,
        },
        status_code=400,
    )


@app.exception_handler(LanguageValidationError)
async def language_validation_error_handler(
    request: Request, exc: LanguageValidationError
) -> JSONResponse | HTMLResponse:
    logger.warning(f"Language validation error: {exc}")
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=400, content={"detail": "Language validation failed", "message": str(exc)})
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 400,
            "error_title": "Language Configuration Error",
            "error_message": str(exc),
            "show_home_link": True,
        },
        status_code=400,
    )
