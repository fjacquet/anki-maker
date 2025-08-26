import asyncio
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from starlette.datastructures import UploadFile as StarletteUploadFile

from ..config import settings
from ..core.document_processor import DocumentProcessingError
from ..core.flashcard_generator import FlashcardGenerator
from ..models.flashcard import Flashcard
from .schemas import ProcessingStatusResponse
from .session_manager import SessionManager, get_session_manager

router = APIRouter()
templates = Jinja2Templates(directory="src/document_to_anki/web/templates")


async def get_files_from_request(request: Request) -> list[UploadFile]:
    """Extract non-empty files from a multipart request."""
    form = await request.form()
    files = form.getlist("files")
    upload_files: list[UploadFile] = []
    for file in files:
        if isinstance(file, StarletteUploadFile) and getattr(file, "filename", ""):
            upload_files.append(file)  # type: ignore[arg-type]
    return upload_files


async def process_files_background(session_id: str, temp_files: list[str], app: Any) -> None:
    """Background task to process uploaded files and generate flashcards."""
    session_manager: SessionManager = app.state.session_manager
    session_data = session_manager.get_session(session_id)
    document_processor = app.state.document_processor
    flashcard_generator: FlashcardGenerator = app.state.flashcard_generator

    try:
        logger.info(f"Starting background processing for session {session_id}")
        session_data["progress"] = 20
        session_data["message"] = "Extracting text from documents..."

        all_text_content: list[str] = []
        source_files: list[str] = []
        for i, temp_file_path in enumerate(temp_files):
            try:
                result = document_processor.process_upload(temp_file_path)
                if result.success:
                    all_text_content.append(result.text_content)
                    source_files.extend(result.source_files)
                else:
                    session_data["errors"].extend(result.errors)
                progress = 20 + (30 * (i + 1) // len(temp_files))
                session_data["progress"] = progress
            except DocumentProcessingError as exc:
                logger.warning(f"Failed to process file {temp_file_path}: {exc}")
                session_data["errors"].append(f"Failed to process file: {exc}")
                continue

        if not all_text_content:
            raise Exception("No text content could be extracted from uploaded files")

        session_data["progress"] = 50
        session_data["message"] = "Generating flashcards using AI..."
        processing_result = await flashcard_generator.generate_flashcards_async(
            text_content=all_text_content, source_files=source_files
        )

        session_data["progress"] = 80
        session_data["message"] = "Finalizing flashcards..."
        session_data["flashcards"] = processing_result.flashcards
        session_data["errors"].extend(processing_result.errors)
        session_data["warnings"] = processing_result.warnings
        session_data["status"] = "completed"
        session_data["progress"] = 100
        session_data["message"] = f"Successfully generated {len(processing_result.flashcards)} flashcards"
    except Exception as exc:  # pragma: no cover - complex background behaviour
        logger.error(f"Background processing failed for session {session_id}: {exc}")
        session_data["status"] = "error"
        session_data["progress"] = 0
        session_data["message"] = f"Processing failed: {exc}"
        session_data["errors"].append(str(exc))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Serve the main application page with language configuration."""
    language_info = settings.get_language_info()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "language_name": language_info.name,
            "language_code": language_info.code,
            "cardlang": settings.cardlang,
        },
    )


@router.post("/api/upload", response_model=ProcessingStatusResponse)
async def upload_files(
    request: Request,
    session_id: str | None = Form(None),
    session_manager: SessionManager = Depends(get_session_manager),
) -> ProcessingStatusResponse:
    """Upload files and start processing them into flashcards."""
    if not session_id:
        session_id = session_manager.create_session()
    session_data = session_manager.get_session(session_id)

    try:
        files = await get_files_from_request(request)
        if not files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

        supported_extensions = {".pdf", ".docx", ".txt", ".md", ".zip"}
        max_file_size = 50 * 1024 * 1024
        temp_files: list[str] = []
        for file in files:
            if not file.filename:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must have a filename")
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in supported_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_extensions)}",
                )
            file_content = await file.read()
            if len(file_content) > max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} is too large. Maximum size: 50MB",
                )
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(file_content)
                temp_files.append(temp_file.name)

        session_data["temp_files"].extend(temp_files)
        session_data["status"] = "processing"
        session_data["message"] = "Processing uploaded files..."
        asyncio.create_task(process_files_background(session_id, temp_files, request.app))

        return ProcessingStatusResponse(
            session_id=session_id,
            status="processing",
            progress=10,
            message="Files uploaded successfully, processing started",
            flashcard_count=0,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Upload failed for session {session_id}: {exc}")
        session_data["status"] = "error"
        session_data["message"] = f"Upload failed: {exc}"
        session_data["errors"].append(str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload processing failed: {exc}"
        ) from exc


@router.get("/api/status/{session_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    session_id: str, session_manager: SessionManager = Depends(get_session_manager)
) -> ProcessingStatusResponse:
    """Get the current processing status for a session."""
    session_data = session_manager.get_session(session_id)
    return ProcessingStatusResponse(
        session_id=session_id,
        status=session_data["status"],
        progress=session_data["progress"],
        message=session_data["message"],
        flashcard_count=len(session_data.get("flashcards", [])),
        errors=session_data.get("errors", []),
    )


@router.delete("/api/sessions/{session_id}")
async def cleanup_session_endpoint(
    session_id: str, session_manager: SessionManager = Depends(get_session_manager)
) -> JSONResponse:
    """Clean up a session and its temporary files."""
    session_manager.get_session(session_id)  # Ensure session exists
    session_manager.cleanup_session(session_id)
    return JSONResponse(content={"success": True, "message": f"Session {session_id} cleaned up successfully"})
