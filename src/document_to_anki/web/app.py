"""
FastAPI web application for document-to-anki conversion.

This module provides a web interface for uploading documents, generating flashcards,
and managing the flashcard creation process through a REST API.
"""

import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel, Field
from starlette.requests import Request

from ..core.document_processor import DocumentProcessor, DocumentProcessingError
from ..core.flashcard_generator import FlashcardGenerator, FlashcardGenerationError
from ..models.flashcard import Flashcard

# Initialize FastAPI app
app = FastAPI(
    title="Document to Anki Converter",
    description="Convert documents to Anki flashcards using AI",
    version="1.0.0",
)

# Global instances
document_processor = DocumentProcessor()
flashcard_generator = FlashcardGenerator()

# Session storage for managing flashcard editing workflows
# In production, this should be replaced with proper session management (Redis, database, etc.)
sessions: Dict[str, Dict[str, Any]] = {}

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
    source_file: Optional[str] = None
    created_at: str


class ProcessingStatusResponse(BaseModel):
    """Response model for processing status."""
    
    session_id: str
    status: str  # "processing", "completed", "error"
    progress: int = Field(ge=0, le=100)
    message: str
    flashcard_count: int = 0
    errors: List[str] = Field(default_factory=list)


class FlashcardEditRequest(BaseModel):
    """Request model for editing flashcards."""
    
    question: str
    answer: str


class FlashcardCreateRequest(BaseModel):
    """Request model for creating new flashcards."""
    
    question: str
    answer: str
    card_type: str
    source_file: Optional[str] = None


class ExportRequest(BaseModel):
    """Request model for CSV export."""
    
    filename: Optional[str] = "flashcards.csv"


# Utility functions
def create_session() -> str:
    """Create a new session ID and initialize session data."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "status": "initialized",
        "progress": 0,
        "message": "Session created",
        "flashcards": [],
        "errors": [],
        "temp_files": [],
    }
    logger.info(f"Created new session: {session_id}")
    return session_id


def get_session(session_id: str) -> Dict[str, Any]:
    """Get session data by ID."""
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return sessions[session_id]


def cleanup_session(session_id: str) -> None:
    """Clean up session data and temporary files."""
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


def flashcard_to_response(flashcard: Flashcard) -> FlashcardResponse:
    """Convert Flashcard model to response format."""
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
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/upload", response_model=ProcessingStatusResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None)
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
        )


async def process_files_background(session_id: str, temp_files: List[str]) -> None:
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
        
        # Complete processing
        session_data["status"] = "completed"
        session_data["progress"] = 100
        session_data["message"] = f"Successfully generated {len(processing_result.flashcards)} flashcards"
        
        logger.info(f"Background processing completed for session {session_id}: {len(processing_result.flashcards)} flashcards generated")
        
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


@app.get("/api/flashcards/{session_id}", response_model=List[FlashcardResponse])
async def get_flashcards(session_id: str) -> List[FlashcardResponse]:
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
        
        # Update the flashcard
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
        )


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
        )


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
                "flashcard": flashcard_to_response(new_flashcard).dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add flashcard to session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add flashcard: {str(e)}"
        )


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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export failed: {'; '.join(summary.get('errors', []))}"
            )
        
        # Prepare filename
        filename = export_request.filename or "flashcards.csv"
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        logger.info(f"Exported {len(flashcards)} flashcards from session {session_id}")
        
        # Return file for download
        return FileResponse(
            path=str(temp_path),
            filename=filename,
            media_type='text/csv',
            background=lambda: temp_path.unlink(missing_ok=True)  # Clean up after download
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


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
        )


@app.get("/api/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "Document to Anki API is running",
            "active_sessions": len(sessions)
        }
    )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
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