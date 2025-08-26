from fastapi.testclient import TestClient

from src.document_to_anki.models.flashcard import Flashcard
from src.document_to_anki.web.app import app


def test_get_flashcards_returns_session_cards():
    client = TestClient(app)
    session_id = app.state.session_manager.create_session()
    card = Flashcard.create("Q?", "A", "qa", "test.txt")
    app.state.session_manager.sessions[session_id]["flashcards"] = [card]
    response = client.get(f"/api/flashcards/{session_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_status_endpoint_uses_session_manager():
    client = TestClient(app)
    session_id = app.state.session_manager.create_session()
    response = client.get(f"/api/status/{session_id}")
    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
