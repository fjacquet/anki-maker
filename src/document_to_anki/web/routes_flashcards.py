from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from ..core.flashcard_generator import FlashcardGenerator
from ..models.flashcard import Flashcard
from .dependencies import get_flashcard_generator, get_session_manager
from .schemas import FlashcardCreateRequest, FlashcardEditRequest, FlashcardResponse
from .session_manager import SessionManager

router = APIRouter()


def flashcard_to_response(flashcard: Flashcard) -> FlashcardResponse:
    """Convert Flashcard model to API response format."""
    return FlashcardResponse(
        id=flashcard.id,
        question=flashcard.question,
        answer=flashcard.answer,
        card_type=flashcard.card_type,
        source_file=flashcard.source_file,
        created_at=flashcard.created_at.isoformat(),
    )


@router.get("/api/flashcards/{session_id}", response_model=list[FlashcardResponse])
async def get_flashcards(
    session_id: str,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> list[FlashcardResponse]:
    """Get all flashcards for a session."""
    session_data = session_manager.get_session(session_id)
    flashcards = session_data.get("flashcards", [])
    return [flashcard_to_response(card) for card in flashcards]


@router.put("/api/flashcards/{session_id}/{flashcard_id}")
async def edit_flashcard(
    session_id: str,
    flashcard_id: str,
    edit_request: FlashcardEditRequest,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    flashcard_generator: Annotated[FlashcardGenerator, Depends(get_flashcard_generator)],
) -> JSONResponse:
    """Edit an existing flashcard."""
    session_data = session_manager.get_session(session_id)
    try:
        flashcards = session_data.get("flashcards", [])
        target_flashcard = next((c for c in flashcards if c.id == flashcard_id), None)
        if not target_flashcard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flashcard {flashcard_id} not found")
        is_valid, error_message = flashcard_generator.validate_flashcard_content(
            edit_request.question, edit_request.answer, target_flashcard.card_type
        )
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        target_flashcard.question = edit_request.question.strip()
        target_flashcard.answer = edit_request.answer.strip()
        logger.info(f"Edited flashcard {flashcard_id} in session {session_id}")
        return JSONResponse(
            content={"success": True, "message": f"Flashcard {flashcard_id[:8]}... updated successfully"}
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to edit flashcard {flashcard_id} in session {session_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to edit flashcard: {exc}"
        ) from exc


@router.delete("/api/flashcards/{session_id}/{flashcard_id}")
async def delete_flashcard(
    session_id: str,
    flashcard_id: str,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> JSONResponse:
    """Delete a flashcard from the session."""
    session_data = session_manager.get_session(session_id)
    try:
        flashcards = session_data.get("flashcards", [])
        for i, card in enumerate(flashcards):
            if card.id == flashcard_id:
                deleted_card = flashcards.pop(i)
                logger.info(f"Deleted flashcard {flashcard_id} from session {session_id}")
                return JSONResponse(
                    content={
                        "success": True,
                        "message": f"Deleted flashcard: {deleted_card.question[:50]}...",
                    }
                )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flashcard {flashcard_id} not found")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to delete flashcard {flashcard_id} from session {session_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete flashcard: {exc}"
        ) from exc


@router.post("/api/flashcards/{session_id}")
async def add_flashcard(
    session_id: str,
    create_request: FlashcardCreateRequest,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    flashcard_generator: Annotated[FlashcardGenerator, Depends(get_flashcard_generator)],
) -> JSONResponse:
    """Add a new flashcard to the session."""
    session_data = session_manager.get_session(session_id)
    try:
        is_valid, error_message = flashcard_generator.validate_flashcard_content(
            create_request.question, create_request.answer, create_request.card_type
        )
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        new_flashcard = Flashcard.create(
            question=create_request.question.strip(),
            answer=create_request.answer.strip(),
            card_type=create_request.card_type,
            source_file=create_request.source_file,
        )
        flashcards = session_data.get("flashcards", [])
        flashcards.append(new_flashcard)
        session_data["flashcards"] = flashcards
        logger.info(f"Added new flashcard to session {session_id}")
        return JSONResponse(
            content={
                "success": True,
                "message": f"Added new flashcard: {new_flashcard.question[:50]}...",
                "flashcard": flashcard_to_response(new_flashcard).model_dump(),
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to add flashcard to session {session_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add flashcard: {exc}"
        ) from exc
