from src.document_to_anki.web.session_manager import SessionManager


def test_session_lifecycle(tmp_path):
    manager = SessionManager()
    session_id = manager.create_session()
    assert session_id in manager.sessions
    session = manager.get_session(session_id)
    assert session["status"] == "initialized"
    manager.cleanup_session(session_id)
    assert session_id not in manager.sessions


def test_cleanup_expired_sessions(tmp_path):
    manager = SessionManager(session_timeout=0)
    session_id = manager.create_session()
    # Manually set last_accessed in past
    manager.sessions[session_id]["last_accessed"] = 0
    import asyncio

    asyncio.run(manager.cleanup_expired_sessions_once())
    assert session_id not in manager.sessions
