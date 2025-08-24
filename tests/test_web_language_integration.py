"""
Integration tests for web interface language configuration consistency.

This module tests that the web interface properly integrates with the language
configuration system and maintains consistency across all operations.
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.document_to_anki.config import Settings
from src.document_to_anki.models.flashcard import Flashcard
from src.document_to_anki.web.app import app


class TestWebLanguageIntegration:
    """Test web interface language configuration integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_settings(self, mocker):
        """Mock settings with different language configurations."""
        return mocker.MagicMock(spec=Settings)

    @pytest.fixture
    def sample_flashcards(self):
        """Create sample flashcards for testing."""
        return [
            Flashcard.create(
                question="What is Python?", answer="A programming language", card_type="qa", source_file="test.txt"
            ),
            Flashcard.create(
                question="Define {{c1::variable}}",
                answer="A storage location with a name",
                card_type="cloze",
                source_file="test.txt",
            ),
        ]

    def test_home_page_displays_language_info(self, client, mocker):
        """Test that home page displays current language configuration."""
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")

        # Mock language info
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "French"
        mock_language_info.code = "fr"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "french"

        response = client.get("/")

        assert response.status_code == 200
        assert "French" in response.text
        assert "fr" in response.text
        assert "📚 Flashcards in French (fr)" in response.text

    def test_language_config_api_endpoint(self, client, mocker):
        """Test language configuration API endpoint."""
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")

        # Mock language info
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "German"
        mock_language_info.code = "de"
        mock_language_info.prompt_key = "german"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "german"

        mock_lang_config = mocker.patch("src.document_to_anki.config.LanguageConfig")
        mock_lang_config.get_supported_languages_list.return_value = [
            "English (en)",
            "French (fr)",
            "German (de)",
            "Italian (it)",
        ]
        mock_lang_config.get_all_language_keys.return_value = [
            "english",
            "en",
            "french",
            "fr",
            "german",
            "de",
            "italian",
            "it",
        ]

        response = client.get("/api/config/language")

        assert response.status_code == 200
        data = response.json()

        assert data["current_language"] == "german"
        assert data["language_name"] == "German"
        assert data["language_code"] == "de"
        assert data["prompt_key"] == "german"
        assert data["status"] == "valid"
        assert "English (en)" in data["supported_languages"]

    def test_language_config_api_validation_error(self, client, mocker):
        """Test language configuration API with validation error."""
        from src.document_to_anki.config import LanguageValidationError

        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")
        mock_settings.get_language_info.side_effect = LanguageValidationError(
            "invalid", ["English (en)", "French (fr)"]
        )

        response = client.get("/api/config/language")

        assert response.status_code == 400
        data = response.json()

        assert data["status"] == "invalid"
        assert "invalid" in data["error"]
        assert "supported_languages" in data

    @pytest.mark.asyncio
    async def test_flashcard_generation_uses_language_config(self, client, sample_flashcards, mocker):
        """Test that flashcard generation uses the configured language."""
        mock_doc_processor = mocker.patch("src.document_to_anki.web.app.document_processor")
        mock_flashcard_gen = mocker.patch("src.document_to_anki.web.app.flashcard_generator")
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")

        # Mock language configuration
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "Italian"
        mock_language_info.code = "it"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "italian"

        # Mock document processing
        mock_result = mocker.MagicMock()
        mock_result.success = True
        mock_result.text_content = "Sample text content"
        mock_result.source_files = ["test.txt"]
        mock_result.errors = []
        mock_doc_processor.process_upload.return_value = mock_result

        # Mock flashcard generation
        mock_processing_result = mocker.MagicMock()
        mock_processing_result.flashcards = sample_flashcards
        mock_processing_result.errors = []
        mock_processing_result.warnings = []
        mock_flashcard_gen.generate_flashcards_async = mocker.AsyncMock(return_value=mock_processing_result)

        # Create a test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp_file:
            temp_file.write("Test content")
            temp_file_path = temp_file.name

        try:
            # Upload file
            with open(temp_file_path, "rb") as f:
                response = client.post("/api/upload", files={"files": ("test.txt", f, "text/plain")})

            assert response.status_code == 200
            data = response.json()
            session_id = data["session_id"]  # noqa: F841

            # Wait for processing to complete (in real scenario)
            # For test, we'll check that the flashcard generator was called
            # The language configuration should be used by the LLMClient within FlashcardGenerator

            # Verify flashcard generation was called
            assert mock_flashcard_gen.generate_flashcards_async.called

        finally:
            # Clean up
            Path(temp_file_path).unlink(missing_ok=True)

    def test_flashcard_operations_maintain_language_consistency(self, client, sample_flashcards, mocker):
        """Test that flashcard CRUD operations maintain language consistency."""
        mock_sessions = mocker.patch("src.document_to_anki.web.app.sessions")
        mock_flashcard_gen = mocker.patch("src.document_to_anki.web.app.flashcard_generator")
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")

        # Mock language configuration
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "French"
        mock_language_info.code = "fr"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "french"

        # Mock session data
        session_id = "test-session"
        mock_sessions.__contains__ = mocker.MagicMock(return_value=True)
        mock_sessions.__getitem__ = mocker.MagicMock(
            return_value={
                "status": "completed",
                "progress": 100,
                "message": "Completed",
                "flashcards": sample_flashcards,
                "errors": [],
                "warnings": [],
                "temp_files": [],
                "created_at": 1234567890,
                "last_accessed": 1234567890,
            }
        )

        # Mock flashcard validation
        mock_flashcard_gen.validate_flashcard_content.return_value = (True, "")

        # Test getting flashcards
        response = client.get(f"/api/flashcards/{session_id}")
        assert response.status_code == 200
        flashcards_data = response.json()
        assert len(flashcards_data) == 2

        # Test editing flashcard
        flashcard_id = sample_flashcards[0].id
        edit_data = {
            "question": "Qu'est-ce que Python?",  # French question
            "answer": "Un langage de programmation",  # French answer
        }

        response = client.put(f"/api/flashcards/{session_id}/{flashcard_id}", json=edit_data)
        assert response.status_code == 200

        # Test adding new flashcard
        new_flashcard_data = {
            "question": "Définir une {{c1::variable}}",  # French cloze
            "answer": "Un emplacement de stockage avec un nom",
            "card_type": "cloze",
            "source_file": "test.txt",
        }

        response = client.post(f"/api/flashcards/{session_id}", json=new_flashcard_data)
        assert response.status_code == 200

    def test_error_handling_for_language_validation_errors(self, client, mocker):
        """Test that language validation errors are properly handled."""
        from src.document_to_anki.config import LanguageValidationError

        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")
        # Mock language validation error
        mock_settings.get_language_info.side_effect = LanguageValidationError(
            "invalid_lang", ["English (en)", "French (fr)", "German (de)", "Italian (it)"]
        )

        # Test API endpoint
        response = client.get("/api/config/language")
        assert response.status_code == 400
        data = response.json()
        assert "invalid_lang" in data["error"]
        assert "supported_languages" in data

        # Test home page (should handle gracefully)
        response = client.get("/")
        assert response.status_code == 400  # Should show error page

    def test_web_interface_language_consistency_across_operations(self, client, sample_flashcards, mocker):
        """Test that all web interface operations use consistent language configuration."""
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")
        mock_sessions = mocker.patch("src.document_to_anki.web.app.sessions")
        mock_flashcard_gen = mocker.patch("src.document_to_anki.web.app.flashcard_generator")

        # Mock consistent language configuration
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "German"
        mock_language_info.code = "de"
        mock_language_info.prompt_key = "german"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "german"

        # Mock session
        session_id = "test-session"
        mock_sessions.__contains__ = mocker.MagicMock(return_value=True)
        mock_sessions.__getitem__ = mocker.MagicMock(
            return_value={
                "status": "completed",
                "progress": 100,
                "message": "Completed",
                "flashcards": sample_flashcards,
                "errors": [],
                "warnings": [],
                "temp_files": [],
                "created_at": 1234567890,
                "last_accessed": 1234567890,
            }
        )

        # Test home page shows German
        response = client.get("/")
        assert response.status_code == 200
        assert "German" in response.text
        assert "de" in response.text

        # Test language config API shows German
        response = client.get("/api/config/language")
        assert response.status_code == 200
        data = response.json()
        assert data["language_name"] == "German"
        assert data["language_code"] == "de"

        # Test flashcard operations (should all use same language context)
        response = client.get(f"/api/flashcards/{session_id}")
        assert response.status_code == 200

        # All operations should be consistent with German language configuration
        # The actual language usage is handled by the LLMClient within FlashcardGenerator

    @pytest.mark.parametrize(
        "language,expected_name,expected_code",
        [
            ("english", "English", "en"),
            ("french", "French", "fr"),
            ("german", "German", "de"),
            ("italian", "Italian", "it"),
            ("en", "English", "en"),
            ("fr", "French", "fr"),
            ("de", "German", "de"),
            ("it", "Italian", "it"),
        ],
    )
    def test_language_configuration_for_all_supported_languages(
        self, client, language, expected_name, expected_code, mocker
    ):
        """Test language configuration for all supported languages."""
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")

        # Mock language info for each supported language
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = expected_name
        mock_language_info.code = expected_code
        mock_language_info.prompt_key = (
            language
            if language in ["english", "french", "german", "italian"]
            else {"en": "english", "fr": "french", "de": "german", "it": "italian"}[language]
        )

        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = language

        # Test home page
        response = client.get("/")
        assert response.status_code == 200
        assert expected_name in response.text
        assert expected_code in response.text

        # Test API endpoint
        response = client.get("/api/config/language")
        assert response.status_code == 200
        data = response.json()
        assert data["language_name"] == expected_name
        assert data["language_code"] == expected_code

    def test_export_functionality_with_language_configuration(self, client, sample_flashcards, mocker):
        """Test that CSV export works correctly with language configuration."""
        mock_sessions = mocker.patch("src.document_to_anki.web.app.sessions")
        mock_flashcard_gen = mocker.patch("src.document_to_anki.web.app.flashcard_generator")
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")

        # Mock language configuration
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "Italian"
        mock_language_info.code = "it"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "italian"

        # Mock session with flashcards
        session_id = "test-session"
        mock_sessions.__contains__ = mocker.MagicMock(return_value=True)
        mock_sessions.__getitem__ = mocker.MagicMock(
            return_value={"status": "completed", "flashcards": sample_flashcards, "last_accessed": 1234567890}
        )

        # Mock successful export
        mock_flashcard_gen.export_to_csv.return_value = (True, {"exported": 2, "errors": []})

        # Test export
        response = client.post(f"/api/export/{session_id}", json={"filename": "italian_flashcards.csv"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Verify export was called with flashcards
        mock_flashcard_gen.export_to_csv.assert_called_once()
        args, kwargs = mock_flashcard_gen.export_to_csv.call_args
        assert len(args[1]) == 2  # Two flashcards exported
