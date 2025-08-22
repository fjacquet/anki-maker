"""
FastAPI web application for document-to-anki conversion.

This module provides a comprehensive web interface for uploading documents, 
generating flashcards, and managing the flashcard creation process through a REST API.

Features:
- Drag-and-drop file upload with real-time validation
- Session-based flashcard management
- Progress tracking for long-running operations
- Interactive flashcard editing interface
- CSV export with detailed statistics
- Comprehensive error handling and user feedback
- Security headers and CORS configuration
- Automatic session cleanup and resource management

API Endpoints:
    GET /: Main application page
    POST /api/upload: Upload files and start processing
    GET /api/status/{session_id}: Get processing status
    GET /api/flashcards/{session_id}: Get all flashcards
    PUT /api/flashcards/{session_id}/{flashcard_id}: Edit flashcard
    DELETE /api/flashcards/{session_id}/{flashcard_id}: Delete flashcard
    POST /api/flashcards/{session_id}: Add new flashcard
    POST /api/export/{session_id}: Export flashcards to CSV
    DELETE /api/sessions/{session_id}: Clean up session
    GET /api/health: Health check endpoint

Classes:
    SecurityHeadersMiddleware: Adds security headers to responses
    FlashcardResponse: Pydantic model for flashcard API responses
    ProcessingStatusResponse: Pydantic model for processing status
    FlashcardEditRequest: Pydantic model for flashcard edit requests
    FlashcardCreateRequest: Pydantic model for flashcard creation
    ExportRequest: Pydantic model for CSV export requests

Functions:
    lifespan: Manage application startup and shutdown
    create_session: Create new session with unique ID
    get_session: Retrieve session data with access time update
    cleanup_session: Clean up session data and temporary files
    cleanup_expired_sessions: Background task for session cleanup
    flashcard_to_response: Convert Flashcard model to API response
    get_files_from_request: Extract files from multipart request
    process_files_background: Background task for file processing

Usage:
    # Start the web server
    uvicorn document_to_anki.web.app:app --host 0.0.0.0 --port 8000
    
    # Or use the CLI command
    document-to-anki-web
"""

import asyncio
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.document_processor import DocumentProcessingError, DocumentProcessor
from ..core.flashcard_generator import FlashcardGenerationError, FlashcardGenerator
from ..models.flashcard import Flashcard


# Security middleware for adding security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    This middleware adds essential security headers to protect against
    common web vulnerabilities:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables XSS filtering
    - Referrer-Policy: Controls referrer information
    - Content-Security-Policy: Prevents XSS and injection attacks
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add security headers to response.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response with added security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        
        return response


# Background task for session cleanup
cleanup_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    
    Handles startup and shutdown tasks:
    - Startup: Initialize background cleanup task for expired sessions
    - Shutdown: Cancel cleanup task and clean up all active sessions
    
    Args:
        app: The FastAPI application instance
        
    Yields:
        None during application runtime
    """
    """Manage application lifespan events."""
    global cleanup_task
    
    # Startup
    logger.info("Starting Document to Anki web application")
    cleanup_task = asyncio.create_task(cleanup_expired_sessions())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Document to Anki web application")
    
    # Cancel cleanup task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    
    # Clean up all sessions
    session_ids = list(sessions.keys())
    for session_id in session_ids:
        cleanup_session(session_id)
    logger.info(f"Cleaned up {len(session_ids)} sessions on shutdown")


# Initialize FastAPI app
app = FastAPI(
    title="Document to Anki Converter",
    description="Convert documents to Anki flashcards using AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)




# Global instances
document_processor = DocumentProcessor()
flashcard_generator = FlashcardGenerator()

# Session storage for managing flashcard editing workflows
# In production, this should be replaced with proper session management (Redis, database, etc.)
sessions: dict[str, dict[str, any]] = {}

# Templates and static files
templates = Jinja2Templates(directory="src/document_to_anki/web/templates")

# Create static directory if it doesn't exist
static_dir = Path("src/document_to_anki/web/static")
static_dir.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Pydantic models for API requests/responses
class FlashcardResponse(BaseModel):
    """Response model for flashcard data."""
    
    id: str
    question: str
    answer: str
    card_type: str
    source_file: str | None = None
    created_at: str


class ProcessingStatusResponse(BaseModel):
    """Response model for processing status."""
    
    session_id: str
    status: str  # "processing", "completed", "error"
    progress: int = Field(ge=0, le=100)
    message: str
    flashcard_count: int = 0
    errors: list[str] = Field(default_factory=list)


class FlashcardEditRequest(BaseModel):
    """Request model for editing flashcards."""
    
    question: str
    answer: str


class FlashcardCreateRequest(BaseModel):
    """Request model for creating new flashcards."""
    
    question: str
    answer: str
    card_type: str
    source_file: str | None = None


class ExportRequest(BaseModel):
    """Request model for CSV export."""
    
    filename: str | None = "flashcards.csv"


# Utility functions
def create_session() -> str:
    """
    Create a new session ID and initialize session data.
    
    Creates a unique session identifier and initializes the session
    with default values for tracking processing status, flashcards,
    errors, warnings, and temporary files.
    
    Returns:
        str: Unique session identifier (UUID4)
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "status": "initialized",
        "progress": 0,
        "message": "Session created",
        "flashcards": [],
        "errors": [],
        "warnings": [],
        "temp_files": [],
        "created_at": time.time(),
        "last_accessed": time.time(),
    }
    logger.info(f"Created new session: {session_id}")
    return session_id


def get_session(session_id: str) -> dict[str, any]:
    """
    Get session data by ID and update last accessed time.
    
    Retrieves session data for the given session ID and updates
    the last accessed timestamp for session timeout management.
    
    Args:
        session_id: The session identifier to retrieve
        
    Returns:
        dict: Session data containing status, flashcards, errors, etc.
        
    Raises:
        HTTPException: If session ID is not found (404)
    """
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Update last accessed time
    sessions[session_id]["last_accessed"] = time.time()
    return sessions[session_id]


def cleanup_session(session_id: str) -> None:
    """
    Clean up session data and temporary files.
    
    Removes session data from memory and deletes any temporary files
    associated with the session. This is called automatically for
    expired sessions and can be called manually via API.
    
    Args:
        session_id: The session identifier to clean up
    """
    if session_id in sessions:
        session_data = sessions[session_id]
        
        # Clean up temporary files
        for temp_file in session_data.get("temp_files", []):
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
        
        # Remove session
        del sessions[session_id]
        logger.info(f"Cleaned up session: {session_id}")


async def cleanup_expired_sessions() -> None:
    """
    Background task to clean up expired sessions.
    
    Runs continuously in the background, checking for sessions that
    haven't been accessed within the timeout period (1 hour) and
    cleaning them up to prevent memory leaks and disk space issues.
    
    The task runs every 10 minutes and logs cleanup activities.
    """
    while True:
        try:
            current_time = time.time()
            session_timeout = 3600  # 1 hour timeout
            
            expired_sessions = []
            for session_id, session_data in sessions.items():
                last_accessed = session_data.get("last_accessed", current_time)
                if current_time - last_accessed > session_timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                logger.info(f"Cleaning up expired session: {session_id}")
                cleanup_session(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
        
        # Sleep for 10 minutes before next cleanup
        await asyncio.sleep(600)


def flashcard_to_response(flashcard: Flashcard) -> FlashcardResponse:
    """
    Convert Flashcard model to API response format.
    
    Transforms internal Flashcard model to the standardized API response
    format with proper serialization of datetime fields.
    
    Args:
        flashcard: The Flashcard model instance to convert
        
    Returns:
        FlashcardResponse: Serialized flashcard data for API response
    """
    return FlashcardResponse(
        id=flashcard.id,
        question=flashcard.question,
        answer=flashcard.answer,
        card_type=flashcard.card_type,
        source_file=flashcard.source_file,
        created_at=flashcard.created_at.isoformat(),
    )


# API Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse(request=request, name="index.html")


async def get_files_from_request(request: Request) -> list[UploadFile]:
    """Extract files from the request, handling empty file uploads."""
    form = await request.form()
    files = form.getlist("files")
    
    # Filter out empty files and convert to UploadFile objects
    upload_files = []
    for file in files:
        if hasattr(file, 'filename') and file.filename:
            upload_files.append(file)
    
    return upload_files

@app.post("/api/upload", response_model=ProcessingStatusResponse)
async def upload_files(
    request: Request,
    session_id: str | None = Form(None)
) -> ProcessingStatusResponse:
    """
    Upload files and start processing them into flashcards.
    
    Supports multiple file uploads including ZIP archives.
    Returns a session ID for tracking progress.
    """
    # Create new session if not provided
    if not session_id:
        session_id = create_session()
    
    session_data = get_session(session_id)
    
    try:
        # Extract files from request
        files = await get_files_from_request(request)
        
        # Validate files
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        
        # Check file types and sizes
        supported_extensions = {".pdf", ".docx", ".txt", ".md", ".zip"}
        max_file_size = 50 * 1024 * 1024  # 50MB
        
        temp_files = []
        
        for file in files:
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must have a filename"
                )
            
            # Check file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in supported_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_extensions)}"
                )
            
            # Check file size
            file_content = await file.read()
            if len(file_content) > max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} is too large. Maximum size: 50MB"
                )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(file_content)
                temp_files.append(temp_file.name)
        
        # Update session with temp files
        session_data["temp_files"].extend(temp_files)
        session_data["status"] = "processing"
        session_data["message"] = "Processing uploaded files..."
        
        # Start background processing
        asyncio.create_task(process_files_background(session_id, temp_files))
        
        return ProcessingStatusResponse(
            session_id=session_id,
            status="processing",
            progress=10,
            message="Files uploaded successfully, processing started",
            flashcard_count=0,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed for session {session_id}: {e}")
        session_data["status"] = "error"
        session_data["message"] = f"Upload failed: {str(e)}"
        session_data["errors"].append(str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        ) from e


async def process_files_background(session_id: str, temp_files: list[str]) -> None:
    """
    Background task to process uploaded files and generate flashcards.
    
    Args:
        session_id: Session identifier
        temp_files: List of temporary file paths to process
    """
    session_data = get_session(session_id)
    
    try:
        logger.info(f"Starting background processing for session {session_id}")
        
        # Update progress
        session_data["progress"] = 20
        session_data["message"] = "Extracting text from documents..."
        
        # Process each file and extract text
        all_text_content = []
        source_files = []
        
        for i, temp_file_path in enumerate(temp_files):
            try:
                # Process the file
                result = document_processor.process_upload(temp_file_path)
                
                if result.success:
                    all_text_content.append(result.text_content)
                    source_files.extend(result.source_files)
                else:
                    session_data["errors"].extend(result.errors)
                
                # Update progress
                progress = 20 + (30 * (i + 1) // len(temp_files))
                session_data["progress"] = progress
                
            except DocumentProcessingError as e:
                logger.warning(f"Failed to process file {temp_file_path}: {e}")
                session_data["errors"].append(f"Failed to process file: {str(e)}")
                continue
        
        if not all_text_content:
            raise Exception("No text content could be extracted from uploaded files")
        
        # Update progress
        session_data["progress"] = 50
        session_data["message"] = "Generating flashcards using AI..."
        
        # Generate flashcards
        processing_result = flashcard_generator.generate_flashcards(
            text_content=all_text_content,
            source_files=source_files
        )
        
        # Update progress
        session_data["progress"] = 80
        session_data["message"] = "Finalizing flashcards..."
        
        # Store flashcards in session
        session_data["flashcards"] = processing_result.flashcards
        session_data["errors"].extend(processing_result.errors)
        session_data["warnings"] = processing_result.warnings
        
        # Complete processing
        session_data["status"] = "completed"
        session_data["progress"] = 100
        session_data["message"] = f"Successfully generated {len(processing_result.flashcards)} flashcards"
        
        logger.info(
            f"Background processing completed for session {session_id}: "
            f"{len(processing_result.flashcards)} flashcards generated"
        )
        
    except Exception as e:
        logger.error(f"Background processing failed for session {session_id}: {e}")
        session_data["status"] = "error"
        session_data["progress"] = 0
        session_data["message"] = f"Processing failed: {str(e)}"
        session_data["errors"].append(str(e))


@app.get("/api/status/{session_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(session_id: str) -> ProcessingStatusResponse:
    """
    Get the current processing status for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Current processing status and progress
    """
    session_data = get_session(session_id)
    
    return ProcessingStatusResponse(
        session_id=session_id,
        status=session_data["status"],
        progress=session_data["progress"],
        message=session_data["message"],
        flashcard_count=len(session_data.get("flashcards", [])),
        errors=session_data.get("errors", []),
    )


@app.get("/api/flashcards/{session_id}", response_model=list[FlashcardResponse])
async def get_flashcards(session_id: str) -> list[FlashcardResponse]:
    """
    Get all flashcards for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of flashcards in the session
    """
    session_data = get_session(session_id)
    
    flashcards = session_data.get("flashcards", [])
    return [flashcard_to_response(card) for card in flashcards]


@app.put("/api/flashcards/{session_id}/{flashcard_id}")
async def edit_flashcard(
    session_id: str,
    flashcard_id: str,
    edit_request: FlashcardEditRequest
) -> JSONResponse:
    """
    Edit an existing flashcard.
    
    Args:
        session_id: Session identifier
        flashcard_id: ID of the flashcard to edit
        edit_request: New question and answer content
        
    Returns:
        Success status and message
    """
    session_data = get_session(session_id)
    
    try:
        # Find the flashcard in session
        flashcards = session_data.get("flashcards", [])
        target_flashcard = None
        
        for card in flashcards:
            if card.id == flashcard_id:
                target_flashcard = card
                break
        
        if not target_flashcard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flashcard {flashcard_id} not found"
            )
        
        # Validate content
        is_valid, error_message = flashcard_generator.validate_flashcard_content(
            edit_request.question,
            edit_request.answer,
            target_flashcard.card_type
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Update the flashcard directly (since it's in the session)
        target_flashcard.question = edit_request.question.strip()
        target_flashcard.answer = edit_request.answer.strip()
        
        logger.info(f"Edited flashcard {flashcard_id} in session {session_id}")
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Flashcard {flashcard_id[:8]}... updated successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to edit flashcard {flashcard_id} in session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit flashcard: {str(e)}"
        ) from e


@app.delete("/api/flashcards/{session_id}/{flashcard_id}")
async def delete_flashcard(session_id: str, flashcard_id: str) -> JSONResponse:
    """
    Delete a flashcard from the session.
    
    Args:
        session_id: Session identifier
        flashcard_id: ID of the flashcard to delete
        
    Returns:
        Success status and message
    """
    session_data = get_session(session_id)
    
    try:
        flashcards = session_data.get("flashcards", [])
        
        # Find and remove the flashcard
        for i, card in enumerate(flashcards):
            if card.id == flashcard_id:
                deleted_card = flashcards.pop(i)
                logger.info(f"Deleted flashcard {flashcard_id} from session {session_id}")
                
                return JSONResponse(
                    content={
                        "success": True,
                        "message": f"Deleted flashcard: {deleted_card.question[:50]}..."
                    }
                )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flashcard {flashcard_id} not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete flashcard {flashcard_id} from session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete flashcard: {str(e)}"
        ) from e


@app.post("/api/flashcards/{session_id}")
async def add_flashcard(
    session_id: str,
    create_request: FlashcardCreateRequest
) -> JSONResponse:
    """
    Add a new flashcard to the session.
    
    Args:
        session_id: Session identifier
        create_request: Flashcard content and metadata
        
    Returns:
        Success status and new flashcard data
    """
    session_data = get_session(session_id)
    
    try:
        # Validate content
        is_valid, error_message = flashcard_generator.validate_flashcard_content(
            create_request.question,
            create_request.answer,
            create_request.card_type
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Create new flashcard
        new_flashcard = Flashcard.create(
            question=create_request.question.strip(),
            answer=create_request.answer.strip(),
            card_type=create_request.card_type,
            source_file=create_request.source_file
        )
        
        # Add to session
        flashcards = session_data.get("flashcards", [])
        flashcards.append(new_flashcard)
        session_data["flashcards"] = flashcards
        
        logger.info(f"Added new flashcard to session {session_id}")
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Added new flashcard: {new_flashcard.question[:50]}...",
                "flashcard": flashcard_to_response(new_flashcard).model_dump()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add flashcard to session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add flashcard: {str(e)}"
        ) from e


@app.post("/api/export/{session_id}")
async def export_flashcards(
    session_id: str,
    export_request: ExportRequest
) -> FileResponse:
    """
    Export flashcards as Anki-compatible CSV file.
    
    Args:
        session_id: Session identifier
        export_request: Export configuration
        
    Returns:
        CSV file download
    """
    session_data = get_session(session_id)
    
    try:
        flashcards = session_data.get("flashcards", [])
        
        if not flashcards:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No flashcards to export"
            )
        
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        # Export flashcards
        success, summary = flashcard_generator.export_to_csv(temp_path, flashcards)
        
        if not success:
            error_details = "; ".join(summary.get("errors", ["Unknown export error"]))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export failed: {error_details}"
            )
        
        # Prepare filename
        filename = export_request.filename or "flashcards.csv"
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        logger.info(f"Exported {len(flashcards)} flashcards from session {session_id}")
        
        # Return file for download
        async def cleanup_temp_file():
            """Clean up temporary file after download."""
            try:
                temp_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")
        
        return FileResponse(
            path=str(temp_path),
            filename=filename,
            media_type='text/csv',
            background=cleanup_temp_file
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        ) from e


@app.delete("/api/sessions/{session_id}")
async def cleanup_session_endpoint(session_id: str) -> JSONResponse:
    """
    Clean up a session and its temporary files.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success confirmation
    """
    try:
        # Check if session exists first
        if session_id not in sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        cleanup_session(session_id)
        return JSONResponse(
            content={
                "success": True,
                "message": f"Session {session_id} cleaned up successfully"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup session: {str(e)}"
        ) from e


@app.get("/api/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "Document to Anki API is running",
            "active_sessions": len(sessions),
            "supported_formats": list(document_processor.get_supported_formats())
        }
    )


@app.get("/api/sessions/{session_id}/statistics")
async def get_session_statistics(session_id: str) -> JSONResponse:
    """Get statistics for a session's flashcards."""
    session_data = get_session(session_id)
    
    flashcards = session_data.get("flashcards", [])
    
    if not flashcards:
        return JSONResponse(
            content={
                "total_count": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "qa_count": 0,
                "cloze_count": 0,
                "source_files": []
            }
        )
    
    # Calculate statistics
    valid_count = sum(1 for card in flashcards if card.validate_content())
    qa_count = sum(1 for card in flashcards if card.card_type == "qa")
    cloze_count = sum(1 for card in flashcards if card.card_type == "cloze")
    source_files = list(set(card.source_file for card in flashcards if card.source_file))
    
    return JSONResponse(
        content={
            "total_count": len(flashcards),
            "valid_count": valid_count,
            "invalid_count": len(flashcards) - valid_count,
            "qa_count": qa_count,
            "cloze_count": cloze_count,
            "source_files": source_files
        }
    )


@app.post("/api/sessions/{session_id}/validate")
async def validate_session_flashcards(session_id: str) -> JSONResponse:
    """Validate all flashcards in a session and return validation results."""
    session_data = get_session(session_id)
    
    flashcards = session_data.get("flashcards", [])
    
    if not flashcards:
        return JSONResponse(
            content={
                "valid_flashcards": [],
                "invalid_flashcards": [],
                "validation_summary": {
                    "total": 0,
                    "valid": 0,
                    "invalid": 0
                }
            }
        )
    
    valid_flashcards = []
    invalid_flashcards = []
    
    for card in flashcards:
        if card.validate_content():
            valid_flashcards.append(flashcard_to_response(card).model_dump())
        else:
            invalid_flashcards.append({
                "id": card.id,
                "question": card.question[:100] + "..." if len(card.question) > 100 else card.question,
                "error": "Validation failed"
            })
    
    return JSONResponse(
        content={
            "valid_flashcards": valid_flashcards,
            "invalid_flashcards": invalid_flashcards,
            "validation_summary": {
                "total": len(flashcards),
                "valid": len(valid_flashcards),
                "invalid": len(invalid_flashcards)
            }
        }
    )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse | HTMLResponse:
    """Handle 404 errors with user-friendly pages."""
    # Check if request is for API endpoint
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={
                "detail": "API endpoint not found",
                "path": request.url.path,
                "method": request.method
            }
        )
    
    # Return HTML error page for web requests
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 404,
            "error_title": "Page Not Found",
            "error_message": "The page you're looking for doesn't exist.",
            "show_home_link": True
        },
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse | HTMLResponse:
    """Handle internal server errors with user-friendly pages."""
    logger.error(f"Internal server error on {request.url.path}: {exc}")
    
    # Check if request is for API endpoint
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": "An unexpected error occurred. Please try again later."
            }
        )
    
    # Return HTML error page for web requests
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 500,
            "error_title": "Server Error",
            "error_message": "An unexpected error occurred. Please try again later.",
            "show_home_link": True
        },
        status_code=500
    )


@app.exception_handler(413)
async def file_too_large_handler(request: Request, exc: HTTPException) -> JSONResponse | HTMLResponse:
    """Handle file too large errors."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=413,
            content={
                "detail": "File too large",
                "message": "The uploaded file exceeds the maximum size limit of 50MB."
            }
        )
    
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 413,
            "error_title": "File Too Large",
            "error_message": "The uploaded file exceeds the maximum size limit of 50MB.",
            "show_home_link": True
        },
        status_code=413
    )


@app.exception_handler(DocumentProcessingError)
async def document_processing_error_handler(
    request: Request, exc: DocumentProcessingError
) -> JSONResponse | HTMLResponse:
    """Handle document processing errors."""
    logger.warning(f"Document processing error: {exc}")
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Document processing failed",
                "message": str(exc)
            }
        )
    
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 400,
            "error_title": "Document Processing Error",
            "error_message": str(exc),
            "show_home_link": True
        },
        status_code=400
    )


@app.exception_handler(FlashcardGenerationError)
async def flashcard_generation_error_handler(
    request: Request, exc: FlashcardGenerationError
) -> JSONResponse | HTMLResponse:
    """Handle flashcard generation errors."""
    logger.warning(f"Flashcard generation error: {exc}")
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Flashcard generation failed",
                "message": str(exc)
            }
        )
    
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "error_code": 400,
            "error_title": "Flashcard Generation Error",
            "error_message": str(exc),
            "show_home_link": True
        },
        status_code=400
    )


# Server runner function
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """
    Run the FastAPI server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    import uvicorn
    
    logger.info(f"Starting Document to Anki web server on {host}:{port}")
    uvicorn.run(
        "document_to_anki.web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)