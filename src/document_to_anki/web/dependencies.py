"""FastAPI dependency providers for the web layer.

Each provider resolves a shared component from ``app.state``, which is populated
during application startup (lifespan) and, in tests, by the ``web_client`` fixture.
Keeping ``app.state`` as the single source of truth lets tests substitute
components via ``app.dependency_overrides`` without monkeypatching internals.
"""

from fastapi import Request

from ..core.document_processor import DocumentProcessor
from ..core.flashcard_generator import FlashcardGenerator
from .session_manager import SessionManager


def get_session_manager(request: Request) -> SessionManager:
    """Return the session manager attached to the application state."""
    return request.app.state.session_manager  # type: ignore[no-any-return]


def get_document_processor(request: Request) -> DocumentProcessor:
    """Return the document processor attached to the application state."""
    return request.app.state.document_processor  # type: ignore[no-any-return]


def get_flashcard_generator(request: Request) -> FlashcardGenerator:
    """Return the flashcard generator attached to the application state."""
    return request.app.state.flashcard_generator  # type: ignore[no-any-return]
