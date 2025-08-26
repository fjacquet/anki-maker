import asyncio
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException, status
from loguru import logger


class SessionManager:
    """Manage in-memory sessions for web workflow."""

    def __init__(self, session_timeout: int = 3600) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout

    def create_session(self) -> str:
        """Create a new session with default metadata."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
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

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Return session data and update last accessed time."""
        if session_id not in self.sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )
        self.sessions[session_id]["last_accessed"] = time.time()
        return self.sessions[session_id]

    def cleanup_session(self, session_id: str) -> None:
        """Remove session and associated temporary files."""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            for temp_file in session_data.get("temp_files", []):
                try:
                    Path(temp_file).unlink(missing_ok=True)
                except Exception as exc:  # pragma: no cover - best effort cleanup
                    logger.warning(f"Failed to clean up temp file {temp_file}: {exc}")
            del self.sessions[session_id]
            logger.info(f"Cleaned up session: {session_id}")

    def cleanup_all_sessions(self) -> None:
        """Clean up all sessions."""
        for session_id in list(self.sessions.keys()):
            self.cleanup_session(session_id)

    async def cleanup_expired_sessions(self) -> None:
        """Continuously remove sessions that exceeded timeout."""
        while True:
            await self.cleanup_expired_sessions_once()
            await asyncio.sleep(600)

    async def cleanup_expired_sessions_once(self) -> None:
        """Remove expired sessions once (useful for testing)."""
        current_time = time.time()
        expired = []
        for session_id, data in list(self.sessions.items()):
            if current_time - data.get("last_accessed", current_time) > self.session_timeout:
                expired.append(session_id)
        for session_id in expired:
            logger.info(f"Cleaning up expired session: {session_id}")
            self.cleanup_session(session_id)

    def __len__(self) -> int:  # pragma: no cover - convenience
        return len(self.sessions)


session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """FastAPI dependency to access the global session manager."""
    return session_manager
