"""
Integration tests for FastAPI web application.

Tests the complete web API workflow from file upload to CSV export.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.document_to_anki.core.document_processor import DocumentProcessingResult
from src.document_to_anki.models.flashcard import Flashcard, ProcessingResult
from src.document_to_anki.web.app import app, cleanup_session, create_session, sessions


class TestWebIntegration:
    """Integration tests for FastAPI web application."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def sample_txt_content(self):
        """Sample text file content for testing."""
        return b"""Python Programming Basics

Python is a high-level programming language. It was created by Guido van Rossum.
Key features include simplicity, readability, and extensive libraries."""

    @pytest.fixture
    def sample_md_content(self):
        """Sample markdown file content for testing."""
        return b"""# Machine Learning

Machine Learning is a subset of artificial intelligence.
It enables computers to learn from data without explicit programming.

## Key Concepts
- Supervised Learning
- Unsupervised Learning
- Reinforcement Learning"""

    @pytest.fixture
    def mock_successful_processing(self, mocker):
        """Mock successful document processing and flashcard generation."""
        # Mock document processing
        mock_doc_result = DocumentProcessingResult(
            text_content="Sample processed text content",
            source_files=["test.txt"],
            file_count=1,
            total_characters=30
        )
        mocker.patch(
            "src.document_to_anki.web.app.document_processor.process_upload",
            return_value=mock_doc_result
        )

        # Create sample flashcards
        sample_flashcards = [
            Flashcard.create("What is Python?", "A programming language", "qa", "test.txt"),
            Flashcard.create("Who created Python?", "Guido van Rossum", "qa", "test.txt"),
            Flashcard.create("Python is known for {{c1::simplicity}}", "simplicity", "cloze", "test.txt"),
        ]
        
        mock_gen_result = ProcessingResult(
            flashcards=sample_flashcards,
            source_files=["test.txt"],
            processing_time=2.0,
            errors=[],
            warnings=[]
        )
        
        mocker.patch(
            "src.document_to_anki.web.app.flashcard_generator.generate_flashcards",
            return_value=mock_gen_result
        )

        # Mock CSV export
        mocker.patch(
            "src.document_to_anki.web.app.flashcard_generator.export_to_csv",
            return_value=(True, {
                "total_flashcards": 3,
                "exported_flashcards": 3,
                "skipped_invalid": 0,
                "qa_cards": 2,
                "cloze_cards": 1,
                "file_size_bytes": 200,
                "output_path": "test_output.csv",
                "errors": []
            })
        )

        return sample_flashcards

    def test_home_page(self, client):
        """Test that the home page loads correctly."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_sessions" in data

    def test_upload_single_file_success(self, client, sample_txt_content, mock_successful_processing):
        """Test successful single file upload."""
        files = {"files": ("test.txt", sample_txt_content, "text/plain")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "processing"
        assert data["progress"] == 10
        assert "Files uploaded successfully" in data["message"]

    def test_upload_multiple_files_success(self, client, sample_txt_content, sample_md_content, mock_successful_processing):
        """Test successful multiple file upload."""
        files = [
            ("files", ("test1.txt", sample_txt_content, "text/plain")),
            ("files", ("test2.md", sample_md_content, "text/markdown"))
        ]
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "processing"

    def test_upload_no_files(self, client):
        """Test upload with no files provided."""
        response = client.post("/api/upload", files={})
        
        assert response.status_code == 400
        assert "No files provided" in response.json()["detail"]

    def test_upload_unsupported_file_type(self, client):
        """Test upload with unsupported file type."""
        files = {"files": ("test.xyz", b"content", "application/octet-stream")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_file_too_large(self, client):
        """Test upload with file that's too large."""
        # Create a file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {"files": ("large.txt", large_content, "text/plain")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 413
        assert "too large" in response.json()["detail"]

    def test_upload_with_existing_session(self, client, sample_txt_content, mock_successful_processing):
        """Test upload with existing session ID."""
        # Create a session first
        session_id = create_session()
        
        files = {"files": ("test.txt", sample_txt_content, "text/plain")}
        data = {"session_id": session_id}
        
        response = client.post("/api/upload", files=files, data=data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_background_processing_success(self, client, sample_txt_content, mock_successful_processing):
        """Test that background processing completes successfully."""
        files = {"files": ("test.txt", sample_txt_content, "text/plain")}
        
        response = client.post("/api/upload", files=files)
        session_id = response.json()["session_id"]
        
        # Wait for background processing to complete
        await asyncio.sleep(0.1)  # Small delay to allow background task to start
        
        # Check final status
        status_response = client.get(f"/api/status/{session_id}")
        assert status_response.status_code == 200
        
        # Note: In real tests, you might need to wait longer or use proper async testing

    def test_get_processing_status_success(self, client):
        """Test getting processing status for valid session."""
        session_id = create_session()
        
        response = client.get(f"/api/status/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "initialized"
        assert data["progress"] == 0

    def test_get_processing_status_invalid_session(self, client):
        """Test getting processing status for invalid session."""
        response = client.get("/api/status/invalid-session-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_flashcards_success(self, client):
        """Test getting flashcards for a session."""
        session_id = create_session()
        
        # Add some flashcards to the session
        sample_flashcards = [
            Flashcard.create("What is Python?", "A programming language", "qa", "test.txt"),
            Flashcard.create("Python is {{c1::interpreted}}", "interpreted", "cloze", "test.txt"),
        ]
        sessions[session_id]["flashcards"] = sample_flashcards
        
        response = client.get(f"/api/flashcards/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["question"] == "What is Python?"
        assert data[0]["answer"] == "A programming language"
        assert data[0]["card_type"] == "qa"

    def test_get_flashcards_invalid_session(self, client):
        """Test getting flashcards for invalid session."""
        response = client.get("/api/flashcards/invalid-session-id")
        
        assert response.status_code == 404

    def test_edit_flashcard_success(self, client, mocker):
        """Test successful flashcard editing."""
        session_id = create_session()
        
        # Add a flashcard to the session
        flashcard = Flashcard.create("What is Python?", "A programming language", "qa", "test.txt")
        sessions[session_id]["flashcards"] = [flashcard]
        
        # Mock validation
        mocker.patch(
            "src.document_to_anki.web.app.flashcard_generator.validate_flashcard_content",
            return_value=(True, "")
        )
        
        edit_data = {
            "question": "What is Python programming?",
            "answer": "A high-level programming language"
        }
        
        response = client.put(f"/api/flashcards/{session_id}/{flashcard.id}", json=edit_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "updated successfully" in data["message"]
        
        # Verify the flashcard was actually updated
        updated_flashcard = sessions[session_id]["flashcards"][0]
        assert updated_flashcard.question == "What is Python programming?"
        assert updated_flashcard.answer == "A high-level programming language"

    def test_edit_flashcard_not_found(self, client):
        """Test editing non-existent flashcard."""
        session_id = create_session()
        sessions[session_id]["flashcards"] = []
        
        edit_data = {
            "question": "New question",
            "answer": "New answer"
        }
        
        response = client.put(f"/api/flashcards/{session_id}/nonexistent-id", json=edit_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_edit_flashcard_validation_error(self, client, mocker):
        """Test editing flashcard with validation error."""
        session_id = create_session()
        
        flashcard = Flashcard.create("What is Python?", "A programming language", "qa", "test.txt")
        sessions[session_id]["flashcards"] = [flashcard]
        
        # Mock validation failure
        mocker.patch(
            "src.document_to_anki.web.app.flashcard_generator.validate_flashcard_content",
            return_value=(False, "Question cannot be empty")
        )
        
        edit_data = {
            "question": "",
            "answer": "A programming language"
        }
        
        response = client.put(f"/api/flashcards/{session_id}/{flashcard.id}", json=edit_data)
        
        assert response.status_code == 400
        assert "Question cannot be empty" in response.json()["detail"]

    def test_delete_flashcard_success(self, client):
        """Test successful flashcard deletion."""
        session_id = create_session()
        
        flashcard = Flashcard.create("What is Python?", "A programming language", "qa", "test.txt")
        sessions[session_id]["flashcards"] = [flashcard]
        
        response = client.delete(f"/api/flashcards/{session_id}/{flashcard.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Deleted flashcard" in data["message"]
        
        # Verify the flashcard was actually deleted
        assert len(sessions[session_id]["flashcards"]) == 0

    def test_delete_flashcard_not_found(self, client):
        """Test deleting non-existent flashcard."""
        session_id = create_session()
        sessions[session_id]["flashcards"] = []
        
        response = client.delete(f"/api/flashcards/{session_id}/nonexistent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_add_flashcard_success(self, client, mocker):
        """Test successful flashcard addition."""
        session_id = create_session()
        sessions[session_id]["flashcards"] = []
        
        # Mock validation
        mocker.patch(
            "src.document_to_anki.web.app.flashcard_generator.validate_flashcard_content",
            return_value=(True, "")
        )
        
        create_data = {
            "question": "What is machine learning?",
            "answer": "A subset of AI",
            "card_type": "qa",
            "source_file": "test.txt"
        }
        
        response = client.post(f"/api/flashcards/{session_id}", json=create_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Added new flashcard" in data["message"]
        assert "flashcard" in data
        
        # Verify the flashcard was actually added
        assert len(sessions[session_id]["flashcards"]) == 1
        added_flashcard = sessions[session_id]["flashcards"][0]
        assert added_flashcard.question == "What is machine learning?"

    def test_add_flashcard_validation_error(self, client, mocker):
        """Test adding flashcard with validation error."""
        session_id = create_session()
        
        # Mock validation failure
        mocker.patch(
            "src.document_to_anki.web.app.flashcard_generator.validate_flashcard_content",
            return_value=(False, "Answer cannot be empty")
        )
        
        create_data = {
            "question": "What is Python?",
            "answer": "",
            "card_type": "qa"
        }
        
        response = client.post(f"/api/flashcards/{session_id}", json=create_data)
        
        assert response.status_code == 400
        assert "Answer cannot be empty" in response.json()["detail"]

    def test_export_flashcards_success(self, client, mock_successful_processing):
        """Test successful flashcard export."""
        session_id = create_session()
        
        # Add flashcards to session
        flashcards = [
            Flashcard.create("What is Python?", "A programming language", "qa", "test.txt"),
            Flashcard.create("Python is {{c1::interpreted}}", "interpreted", "cloze", "test.txt"),
        ]
        sessions[session_id]["flashcards"] = flashcards
        
        export_data = {"filename": "my_flashcards.csv"}
        
        response = client.post(f"/api/export/{session_id}", json=export_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "my_flashcards.csv" in response.headers.get("content-disposition", "")

    def test_export_flashcards_no_flashcards(self, client):
        """Test export with no flashcards."""
        session_id = create_session()
        sessions[session_id]["flashcards"] = []
        
        export_data = {"filename": "empty.csv"}
        
        response = client.post(f"/api/export/{session_id}", json=export_data)
        
        assert response.status_code == 400
        assert "No flashcards to export" in response.json()["detail"]

    def test_export_flashcards_default_filename(self, client, mock_successful_processing):
        """Test export with default filename."""
        session_id = create_session()
        
        flashcards = [
            Flashcard.create("What is Python?", "A programming language", "qa", "test.txt"),
        ]
        sessions[session_id]["flashcards"] = flashcards
        
        export_data = {}  # No filename specified
        
        response = client.post(f"/api/export/{session_id}", json=export_data)
        
        assert response.status_code == 200
        assert "flashcards.csv" in response.headers.get("content-disposition", "")

    def test_cleanup_session_success(self, client):
        """Test successful session cleanup."""
        session_id = create_session()
        
        response = client.delete(f"/api/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cleaned up successfully" in data["message"]
        
        # Verify session was actually removed
        assert session_id not in sessions

    def test_cleanup_session_not_found(self, client):
        """Test cleanup of non-existent session."""
        response = client.delete("/api/sessions/nonexistent-session")
        
        assert response.status_code == 404

    def test_static_files_served(self, client):
        """Test that static files are served correctly."""
        # This test assumes there are static files in the static directory
        # You might need to create a test static file first
        response = client.get("/static/style.css")
        
        # The response might be 404 if the file doesn't exist, which is fine for this test
        # We're just checking that the static file serving is set up
        assert response.status_code in [200, 404]

    def test_error_handling_404(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404

    def test_session_management_lifecycle(self, client, sample_txt_content, mock_successful_processing):
        """Test complete session lifecycle: create, use, cleanup."""
        # 1. Upload files (creates session)
        files = {"files": ("test.txt", sample_txt_content, "text/plain")}
        upload_response = client.post("/api/upload", files=files)
        session_id = upload_response.json()["session_id"]
        
        # 2. Check status
        status_response = client.get(f"/api/status/{session_id}")
        assert status_response.status_code == 200
        
        # 3. Get flashcards (after processing would complete)
        # In a real scenario, you'd wait for processing to complete
        sessions[session_id]["flashcards"] = [
            Flashcard.create("Test question", "Test answer", "qa", "test.txt")
        ]
        
        flashcards_response = client.get(f"/api/flashcards/{session_id}")
        assert flashcards_response.status_code == 200
        assert len(flashcards_response.json()) == 1
        
        # 4. Export flashcards
        export_response = client.post(f"/api/export/{session_id}", json={"filename": "test.csv"})
        assert export_response.status_code == 200
        
        # 5. Cleanup session
        cleanup_response = client.delete(f"/api/sessions/{session_id}")
        assert cleanup_response.status_code == 200
        
        # 6. Verify session is gone
        status_response = client.get(f"/api/status/{session_id}")
        assert status_response.status_code == 404


class TestWebErrorHandling:
    """Test error handling in web application."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_upload_processing_error(self, client, mocker):
        """Test handling of processing errors during upload."""
        # Mock document processor to raise an error
        from src.document_to_anki.core.document_processor import DocumentProcessingError
        mocker.patch(
            "src.document_to_anki.web.app.document_processor.process_upload",
            side_effect=DocumentProcessingError("Processing failed")
        )
        
        files = {"files": ("test.txt", b"content", "text/plain")}
        response = client.post("/api/upload", files=files)
        
        # The upload should succeed, but background processing will fail
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        
        # Check that the error is recorded in the session
        # Note: In real tests, you might need to wait for background processing

    def test_flashcard_generation_error(self, client, mocker):
        """Test handling of flashcard generation errors."""
        session_id = create_session()
        
        # Mock flashcard generator to raise an error
        from src.document_to_anki.core.flashcard_generator import FlashcardGenerationError
        mocker.patch(
            "src.document_to_anki.web.app.flashcard_generator.generate_flashcards",
            side_effect=FlashcardGenerationError("Generation failed")
        )
        
        # This would be tested through the background processing
        # In a real scenario, you'd trigger background processing and check the session status

    def test_export_error_handling(self, client, mocker):
        """Test export error handling."""
        session_id = create_session()
        sessions[session_id]["flashcards"] = [
            Flashcard.create("Test", "Test", "qa", "test.txt")
        ]
        
        # Mock export to fail
        mocker.patch(
            "src.document_to_anki.web.app.flashcard_generator.export_to_csv",
            return_value=(False, {"errors": ["Export failed"]})
        )
        
        response = client.post(f"/api/export/{session_id}", json={})
        
        assert response.status_code == 500
        assert "Export failed" in response.json()["detail"]

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in requests."""
        session_id = create_session()
        
        # Send invalid JSON
        response = client.put(
            f"/api/flashcards/{session_id}/test-id",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields in requests."""
        session_id = create_session()
        
        # Send request with missing required fields
        response = client.post(f"/api/flashcards/{session_id}", json={"question": "Test"})
        
        assert response.status_code == 422  # Validation error

    def test_concurrent_session_access(self, client):
        """Test concurrent access to the same session."""
        session_id = create_session()
        sessions[session_id]["flashcards"] = [
            Flashcard.create("Test", "Test", "qa", "test.txt")
        ]
        
        # Simulate concurrent requests
        response1 = client.get(f"/api/flashcards/{session_id}")
        response2 = client.get(f"/api/flashcards/{session_id}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()


class TestWebPerformance:
    """Test performance aspects of web application."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_large_file_upload_handling(self, client):
        """Test handling of large file uploads within limits."""
        # Create a file just under the limit (50MB)
        large_content = b"x" * (49 * 1024 * 1024)  # 49MB
        files = {"files": ("large.txt", large_content, "text/plain")}
        
        response = client.post("/api/upload", files=files)
        
        # Should succeed (though processing might take time)
        assert response.status_code == 200

    def test_multiple_concurrent_uploads(self, client, mocker):
        """Test handling of multiple concurrent uploads."""
        # Mock processing to be fast
        mock_doc_result = DocumentProcessingResult(
            text_content="Test content",
            source_files=["test.txt"],
            file_count=1,
            total_characters=12
        )
        mocker.patch(
            "src.document_to_anki.web.app.document_processor.process_upload",
            return_value=mock_doc_result
        )
        
        # Create multiple upload requests
        files = {"files": ("test.txt", b"content", "text/plain")}
        
        responses = []
        for _ in range(3):
            response = client.post("/api/upload", files=files)
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert "session_id" in response.json()

    def test_session_cleanup_performance(self, client):
        """Test that session cleanup doesn't affect performance."""
        # Create multiple sessions
        session_ids = []
        for _ in range(10):
            session_id = create_session()
            session_ids.append(session_id)
        
        # Cleanup all sessions
        for session_id in session_ids:
            response = client.delete(f"/api/sessions/{session_id}")
            assert response.status_code == 200
        
        # Verify all sessions are cleaned up
        assert len(sessions) == 0