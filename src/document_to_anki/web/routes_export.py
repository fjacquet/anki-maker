import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from loguru import logger
from starlette.background import BackgroundTask

from ..core.flashcard_generator import FlashcardGenerator
from .schemas import ExportRequest
from .session_manager import SessionManager, get_session_manager

router = APIRouter()


def get_flashcard_generator(request: Request) -> FlashcardGenerator:
    return request.app.state.flashcard_generator


@router.post("/api/export/{session_id}")
async def export_flashcards(
    session_id: str,
    export_request: ExportRequest,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    flashcard_generator: Annotated[FlashcardGenerator, Depends(get_flashcard_generator)],
) -> FileResponse:
    """Export flashcards as an Anki-compatible CSV file."""
    session_data = session_manager.get_session(session_id)
    try:
        flashcards = session_data.get("flashcards", [])
        if not flashcards:
            raise HTTPException(status_code=400, detail="No flashcards to export")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        success, summary = flashcard_generator.export_to_csv(temp_path, flashcards)
        if not success:
            error_details = "; ".join(summary.get("errors", ["Unknown export error"]))
            raise HTTPException(status_code=500, detail=f"Export failed: {error_details}")
        filename = export_request.filename or "flashcards.csv"
        if not filename.endswith(".csv"):
            filename += ".csv"
        logger.info(f"Exported {len(flashcards)} flashcards from session {session_id}")

        def cleanup_temp_file() -> None:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception as exc:  # pragma: no cover - best effort cleanup
                logger.warning(f"Failed to cleanup temp file {temp_path}: {exc}")

        return FileResponse(
            path=str(temp_path),
            filename=filename,
            media_type="text/csv",
            background=BackgroundTask(cleanup_temp_file),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Export failed for session {session_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}") from exc
