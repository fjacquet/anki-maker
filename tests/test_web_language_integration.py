"""
Integration tests for web interface language configuration consistency.

This module tests that the web interface properly integrates with the language
configuration system and maintains consistency across all operations.
"""

import tempfile
from pathlib import Path

import pytest

from src.document_to_anki.config import Settings
from src.document_to_anki.models.flashcard import Flashcard, ProcessingResult
from src.document_to_anki.web.app import app
from src.document_to_anki.web.dependencies import get_flashcard_generator


class TestWebLanguageIntegration:
    """Test web interface language configuration integration."""

    @pytest.fixture
    def client(self, web_client):
        """Use the shared web client fixture."""
        return web_client

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

        # FastAPI converts HTTPException detail to this format
        assert "detail" in data
        detail = data["detail"]
        assert detail["status"] == "invalid"
        assert "invalid" in detail["error"]
        assert "supported_languages" in detail

    @pytest.mark.asyncio
    async def test_flashcard_generation_uses_language_config(self, client, sample_flashcards, mocker):
        """Background processing invokes the configured flashcard generator."""
        from src.document_to_anki.web.routes_upload import process_files_background

        # Configure the offline generator double held in app.state (the single source of truth).
        processing_result = ProcessingResult(
            flashcards=sample_flashcards, source_files=["test.txt"], processing_time=0.0, errors=[], warnings=[]
        )
        client.app.state.flashcard_generator.generate_flashcards_async = mocker.AsyncMock(
            return_value=processing_result
        )

        # Create a test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp_file:
            temp_file.write("Test content")
            temp_file_path = temp_file.name

        try:
            session_id = client.app.state.session_manager.create_session()

            # Run the background task deterministically (no create_task timing race).
            await process_files_background(session_id, [temp_file_path], client.app)

            # Verify flashcard generation was called
            assert client.app.state.flashcard_generator.generate_flashcards_async.called

        finally:
            # Clean up
            Path(temp_file_path).unlink(missing_ok=True)

    def test_flashcard_operations_maintain_language_consistency(self, client, sample_flashcards, mocker):
        """Test that flashcard CRUD operations maintain language consistency."""
        # Create a real session instead of mocking
        session_id = app.state.session_manager.create_session()
        app.state.session_manager.sessions[session_id]["status"] = "completed"
        app.state.session_manager.sessions[session_id]["flashcards"] = sample_flashcards

        mock_flashcard_gen = mocker.patch("src.document_to_anki.web.app.flashcard_generator")
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")

        # Mock language configuration
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "French"
        mock_language_info.code = "fr"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "french"

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

        # Mock settings in both locations where it's used
        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")
        mocker.patch("src.document_to_anki.web.routes_upload.settings", mock_settings)
        # Mock language validation error
        mock_settings.get_language_info.side_effect = LanguageValidationError(
            "invalid_lang", ["English (en)", "French (fr)", "German (de)", "Italian (it)"]
        )

        # Test API endpoint
        response = client.get("/api/config/language")
        assert response.status_code == 400
        data = response.json()
        # FastAPI converts HTTPException detail to this format
        assert "detail" in data
        detail = data["detail"]
        assert "invalid_lang" in detail["error"]
        assert "supported_languages" in detail

        # Test home page (should handle gracefully)
        response = client.get("/")
        assert response.status_code == 400  # Should show error page via exception handler

    def test_web_interface_language_consistency_across_operations(self, client, sample_flashcards, mocker):
        """Test that all web interface operations use consistent language configuration."""
        # Mock settings in both modules that read it: the home page (routes_upload)
        # and the /api/config/language endpoint (web.app).
        mock_settings = mocker.patch("src.document_to_anki.web.routes_upload.settings")
        mocker.patch("src.document_to_anki.web.app.settings", mock_settings)

        # Mock consistent language configuration
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "German"
        mock_language_info.code = "de"
        mock_language_info.prompt_key = "german"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "german"

        # Real session in app.state (the single source of truth for the dependency).
        session_id = client.app.state.session_manager.create_session()
        client.app.state.session_manager.sessions[session_id]["flashcards"] = sample_flashcards

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
        # Mock settings in both modules that read it: the home page (routes_upload)
        # and the /api/config/language endpoint (web.app).
        mock_settings = mocker.patch("src.document_to_anki.web.routes_upload.settings")
        mocker.patch("src.document_to_anki.web.app.settings", mock_settings)

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
        # Create a real session instead of mocking
        session_id = app.state.session_manager.create_session()
        app.state.session_manager.sessions[session_id]["status"] = "completed"
        app.state.session_manager.sessions[session_id]["flashcards"] = sample_flashcards

        # Inject a generator double via the FastAPI dependency-override seam.
        mock_flashcard_gen = mocker.MagicMock()
        mock_flashcard_gen.export_to_csv.return_value = (True, {"exported": 2, "errors": []})
        client.app.dependency_overrides[get_flashcard_generator] = lambda: mock_flashcard_gen

        mock_settings = mocker.patch("src.document_to_anki.web.app.settings")

        # Mock language configuration
        mock_language_info = mocker.MagicMock()
        mock_language_info.name = "Italian"
        mock_language_info.code = "it"
        mock_settings.get_language_info.return_value = mock_language_info
        mock_settings.cardlang = "italian"

        # Test export
        response = client.post(f"/api/export/{session_id}", json={"filename": "italian_flashcards.csv"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Verify export was called with flashcards
        mock_flashcard_gen.export_to_csv.assert_called_once()
        args, kwargs = mock_flashcard_gen.export_to_csv.call_args
        assert len(args[1]) == 2  # Two flashcards exported
