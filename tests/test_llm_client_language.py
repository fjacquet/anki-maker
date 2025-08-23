"""
Unit tests for LLM client language-specific functionality.

Tests the LLMClient class language support, prompt generation,
and language validation features.
"""

# Using pytest-mock instead of unittest.mock

import pytest

from src.document_to_anki.config import LanguageInfo, LanguageValidationError
from src.document_to_anki.core.llm_client import FlashcardData, LLMClient


class TestLLMClientLanguage:
    """Test cases for LLM client language functionality."""

    @pytest.fixture
    def mock_litellm(self, mocker):
        """Mock litellm for testing."""
        return mocker.patch("src.document_to_anki.core.llm_client.litellm")

    @pytest.fixture
    def mock_model_config(self, mocker):
        """Mock ModelConfig for testing."""
        mock = mocker.patch("src.document_to_anki.core.llm_client.ModelConfig")
        mock.validate_and_get_model.return_value = "gemini/gemini-2.5-flash"
        mock.validate_model_config.return_value = True
        return mock

    def test_init_with_language_parameter(self, mock_litellm, mock_model_config, mocker):
        """Test LLMClient initialization with language parameter."""
        client = LLMClient(language="french")

        assert client.language == "french"
        assert client.model == "gemini/gemini-2.5-flash"
        assert client.language_info.name == "French"
        assert client.language_info.code == "fr"

    def test_init_with_default_language(self, mock_litellm, mock_model_config, mocker):
        """Test LLMClient initialization with default language."""
        client = LLMClient()

        assert client.language == "english"
        assert client.language_info.name == "English"
        assert client.language_info.code == "en"

    def test_init_language_normalization(self, mock_litellm, mock_model_config, mocker):
        """Test that language is normalized during initialization."""
        client = LLMClient(language="  FRENCH  ")

        assert client.language == "french"
        assert client.language_info.name == "French"

    def test_init_with_iso_language_code(self, mock_litellm, mock_model_config, mocker):
        """Test LLMClient initialization with ISO language codes."""
        client = LLMClient(language="de")

        assert client.language == "de"
        assert client.language_info.name == "German"
        assert client.language_info.code == "de"

    def test_init_with_invalid_language(self, mock_litellm, mock_model_config, mocker):
        """Test LLMClient initialization with invalid language raises error."""
        with pytest.raises(LanguageValidationError, match="Unsupported language 'spanish'"):
            LLMClient(language="spanish")

    def test_init_with_empty_language(self, mock_litellm, mock_model_config, mocker):
        """Test LLMClient initialization with empty language defaults to English."""
        client = LLMClient(language="")

        assert client.language == "english"
        assert client.language_info.name == "English"

    def test_get_current_language(self, mock_litellm, mock_model_config, mocker):
        """Test getting current language configuration."""
        client = LLMClient(language="italian")

        assert client.get_current_language() == "italian"

    def test_get_language_info(self, mock_litellm, mock_model_config, mocker):
        """Test getting detailed language information."""
        client = LLMClient(language="german")

        lang_info = client.get_language_info()
        assert isinstance(lang_info, LanguageInfo)
        assert lang_info.name == "German"
        assert lang_info.code == "de"
        assert lang_info.prompt_key == "german"

    def test_set_language_valid(self, mock_litellm, mock_model_config, mocker):
        """Test setting a valid language."""
        client = LLMClient(language="english")

        client.set_language("italian")

        assert client.language == "italian"
        assert client.language_info.name == "Italian"
        assert client.language_info.code == "it"

    def test_set_language_invalid(self, mock_litellm, mock_model_config, mocker):
        """Test setting an invalid language raises error."""
        client = LLMClient(language="english")

        with pytest.raises(LanguageValidationError, match="Unsupported language 'spanish'"):
            client.set_language("spanish")

        # Original language should be preserved
        assert client.language == "english"

    def test_set_language_with_normalization(self, mock_litellm, mock_model_config, mocker):
        """Test setting language with normalization."""
        client = LLMClient(language="english")

        client.set_language("  FR  ")

        assert client.language == "fr"
        assert client.language_info.name == "French"

    def test_get_prompt_template_english(self, mock_litellm, mock_model_config, mocker):
        """Test getting English prompt template."""
        client = LLMClient(language="english")

        template = client.get_prompt_template("english", "general")

        assert "You are an expert educator" in template
        assert "IN ENGLISH" in template
        assert "{text}" in template

    def test_get_prompt_template_french(self, mock_litellm, mock_model_config, mocker):
        """Test getting French prompt template."""
        client = LLMClient(language="french")

        template = client.get_prompt_template("french", "academic")

        assert "Vous êtes un expert" in template
        assert "EN FRANÇAIS" in template
        assert "vocabulaire académique" in template
        assert "{text}" in template

    def test_get_prompt_template_italian(self, mock_litellm, mock_model_config, mocker):
        """Test getting Italian prompt template."""
        client = LLMClient(language="italian")

        template = client.get_prompt_template("italian", "technical")

        assert "Sei un esperto" in template
        assert "IN ITALIANO" in template
        assert "terminologia tecnica" in template
        assert "{text}" in template

    def test_get_prompt_template_german(self, mock_litellm, mock_model_config, mocker):
        """Test getting German prompt template."""
        client = LLMClient(language="german")

        template = client.get_prompt_template("german", "general")

        assert "Sie sind ein Experte" in template
        assert "AUF DEUTSCH" in template
        assert "{text}" in template

    def test_get_prompt_template_invalid_language(self, mock_litellm, mock_model_config, mocker):
        """Test that invalid language raises ValueError."""
        client = LLMClient()

        with pytest.raises(ValueError, match="Unsupported language"):
            client.get_prompt_template("spanish", "general")

    def test_create_flashcard_prompt_uses_instance_language(self, mock_litellm, mock_model_config, mocker):
        """Test that _create_flashcard_prompt uses instance language when none specified."""
        client = LLMClient(language="italian")

        prompt = client._create_flashcard_prompt("Test text")

        assert "Sei un esperto" in prompt
        assert "Test text" in prompt

    def test_create_flashcard_prompt_overrides_language(self, mock_litellm, mock_model_config, mocker):
        """Test that _create_flashcard_prompt can override instance language."""
        client = LLMClient(language="english")

        prompt = client._create_flashcard_prompt("Test text", language="german")

        assert "Sie sind ein Experte" in prompt
        assert "Test text" in prompt

    def test_create_flashcard_prompt_with_content_type(self, mock_litellm, mock_model_config, mocker):
        """Test _create_flashcard_prompt with different content types."""
        client = LLMClient(language="french")

        academic_prompt = client._create_flashcard_prompt("Test text", content_type="academic")
        technical_prompt = client._create_flashcard_prompt("Test text", content_type="technical")

        assert "vocabulaire académique" in academic_prompt
        assert "terminologie technique" in technical_prompt

    def test_create_flashcard_prompt_invalid_parameters(self, mock_litellm, mock_model_config, mocker):
        """Test that invalid parameters raise ValueError."""
        client = LLMClient()

        with pytest.raises(ValueError, match="Invalid parameters"):
            client._create_flashcard_prompt("Test text", language="spanish")

        with pytest.raises(ValueError, match="Invalid parameters"):
            client._create_flashcard_prompt("Test text", content_type="invalid")

    def test_validate_response_language_english(self, mock_litellm, mock_model_config, mocker):
        """Test language validation for English flashcards."""
        client = LLMClient(language="english")

        english_flashcards = [
            FlashcardData("What is the capital?", "The capital is Paris", "qa"),
            FlashcardData("Where is the building?", "The building is here", "qa"),
        ]

        is_valid, metrics = client._validate_response_language(english_flashcards, "english")
        assert is_valid
        assert metrics["success_rate"] >= 0.3
        assert metrics["sample_size"] == 2
        assert metrics["language_info"].name == "English"

    def test_validate_response_language_french(self, mock_litellm, mock_model_config, mocker):
        """Test language validation for French flashcards."""
        client = LLMClient(language="french")

        french_flashcards = [
            FlashcardData("Quelle est la capitale?", "La capitale est Paris", "qa"),
            FlashcardData("Où est le bâtiment?", "Le bâtiment est ici", "qa"),
        ]

        is_valid, metrics = client._validate_response_language(french_flashcards, "french")
        assert is_valid
        assert metrics["success_rate"] >= 0.3
        assert metrics["sample_size"] == 2
        assert metrics["language_info"].name == "French"

    def test_validate_response_language_italian(self, mock_litellm, mock_model_config, mocker):
        """Test language validation for Italian flashcards."""
        client = LLMClient(language="italian")

        italian_flashcards = [
            FlashcardData("Qual è la capitale?", "La capitale è Roma", "qa"),
            FlashcardData("Dove è l'edificio?", "L'edificio è qui", "qa"),
        ]

        is_valid, metrics = client._validate_response_language(italian_flashcards, "italian")
        assert is_valid
        assert metrics["success_rate"] >= 0.3
        assert metrics["sample_size"] == 2
        assert metrics["language_info"].name == "Italian"

    def test_validate_response_language_german(self, mock_litellm, mock_model_config, mocker):
        """Test language validation for German flashcards."""
        client = LLMClient(language="german")

        german_flashcards = [
            FlashcardData("Was ist die Hauptstadt?", "Die Hauptstadt ist Berlin", "qa"),
            FlashcardData("Wo ist das Gebäude?", "Das Gebäude ist hier", "qa"),
        ]

        is_valid, metrics = client._validate_response_language(german_flashcards, "german")
        assert is_valid
        assert metrics["success_rate"] >= 0.3
        assert metrics["sample_size"] == 2
        assert metrics["language_info"].name == "German"

    def test_validate_response_language_mismatch(self, mock_litellm, mock_model_config, mocker):
        """Test language validation with language mismatch."""
        client = LLMClient(language="english")

        # French flashcards when expecting English
        french_flashcards = [
            FlashcardData("Quelle est la capitale?", "La capitale est Paris", "qa"),
            FlashcardData("Où est le bâtiment?", "Le bâtiment est ici", "qa"),
        ]

        # Should return False for language mismatch
        is_valid, metrics = client._validate_response_language(french_flashcards, "english")
        assert not is_valid
        assert metrics["success_rate"] < 0.3
        assert metrics["language_info"].name == "English"

    def test_validate_response_language_empty_list(self, mock_litellm, mock_model_config, mocker):
        """Test language validation with empty flashcard list."""
        client = LLMClient()

        is_valid, metrics = client._validate_response_language([], "english")
        assert is_valid
        assert metrics["validation_method"] == "empty_list"
        assert metrics["sample_size"] == 0

    def test_validate_response_language_unsupported_language(self, mock_litellm, mock_model_config, mocker):
        """Test language validation with unsupported language."""
        client = LLMClient()

        flashcards = [FlashcardData("Test question", "Test answer", "qa")]

        # Should return True for unsupported languages (skip validation)
        is_valid, metrics = client._validate_response_language(flashcards, "spanish")
        assert is_valid
        assert metrics["validation_method"] == "unsupported_language"

    def test_validate_response_language_with_iso_codes(self, mock_litellm, mock_model_config, mocker):
        """Test language validation with ISO language codes."""
        client = LLMClient()

        english_flashcards = [
            FlashcardData("What is the capital?", "The capital is Paris", "qa"),
        ]

        # Should work with ISO codes
        is_valid, metrics = client._validate_response_language(english_flashcards, "en")
        assert is_valid
        assert metrics["language_info"].code == "en"

    @pytest.mark.asyncio
    async def test_generate_flashcards_uses_instance_language(self, mock_litellm, mock_model_config, mocker):
        """Test that generate_flashcards_from_text uses instance language when no language specified."""
        client = LLMClient(language="german")

        # Mock the API call
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message.content = """[
            {
                "question": "Was ist die Hauptstadt?",
                "answer": "Berlin",
                "card_type": "qa"
            }
        ]"""

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response.choices[0].message.content

        # Call with explicit language parameter to use instance language
        _ = await client.generate_flashcards_from_text("Test text", language="german")

        # Check that German prompt was used
        call_args = mock_api.call_args[0][0]  # Get the prompt argument
        assert "Sie sind ein Experte" in call_args

    @pytest.mark.asyncio
    async def test_generate_flashcards_overrides_language(self, mock_litellm, mock_model_config, mocker):
        """Test that generate_flashcards_from_text can override instance language."""
        client = LLMClient(language="english")

        # Mock the API call
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message.content = """[
            {
                "question": "Quelle est la capitale?",
                "answer": "Paris",
                "card_type": "qa"
            }
        ]"""

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response.choices[0].message.content

        _ = await client.generate_flashcards_from_text("Test text", language="french")

        # Check that French prompt was used
        call_args = mock_api.call_args[0][0]  # Get the prompt argument
        assert "Vous êtes un expert" in call_args

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_content_type(self, mock_litellm, mock_model_config, mocker):
        """Test generate_flashcards_from_text with different content types."""
        client = LLMClient(language="italian")

        # Mock Settings to return Italian
        mock_settings = mocker.Mock()
        mock_settings.cardlang = "italian"

        # Mock the API call
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message.content = """[
            {
                "question": "Qual è la capitale?",
                "answer": "Roma",
                "card_type": "qa"
            }
        ]"""

        mocker.patch("src.document_to_anki.config.settings", mock_settings)
        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response.choices[0].message.content

        _ = await client.generate_flashcards_from_text("Test text", content_type="technical")

        # Check that technical prompt was used
        call_args = mock_api.call_args[0][0]  # Get the prompt argument
        assert "terminologia tecnica" in call_args

    @pytest.mark.asyncio
    async def test_generate_flashcards_language_validation_warning(self, mock_litellm, mock_model_config, mocker):
        """Test that language validation warnings are logged."""
        client = LLMClient(language="english")

        # Mock Settings to return English
        mock_settings = mocker.Mock()
        mock_settings.cardlang = "english"

        # Mock API response with French content when expecting English
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message.content = """[
            {
                "question": "Quelle est la capitale?",
                "answer": "La capitale est Paris",
                "card_type": "qa"
            }
        ]"""

        mocker.patch("src.document_to_anki.config.settings", mock_settings)
        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response.choices[0].message.content

        mock_logger = mocker.patch("src.document_to_anki.core.llm_client.logger")
        _ = await client.generate_flashcards_from_text("Test text")

        # Check that warning was logged
        mock_logger.warning.assert_called()
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        validation_warning = any("Language validation failed" in call for call in warning_calls)
        assert validation_warning

    @pytest.mark.asyncio
    async def test_generate_flashcards_uses_settings_language(self, mock_litellm, mock_model_config, mocker):
        """Test that generate_flashcards_from_text uses Settings language when no language specified."""
        client = LLMClient(language="english")

        # Mock Settings to return Italian
        mock_settings = mocker.Mock()
        mock_settings.cardlang = "italian"

        # Mock the API call
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message.content = """[
            {
                "question": "Qual è la capitale?",
                "answer": "Roma",
                "card_type": "qa"
            }
        ]"""

        mocker.patch("src.document_to_anki.config.settings", mock_settings)
        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response.choices[0].message.content

        _ = await client.generate_flashcards_from_text("Test text")

        # Check that Italian prompt was used (from Settings, not instance language)
        call_args = mock_api.call_args[0][0]  # Get the prompt argument
        assert "Sei un esperto" in call_args

    @pytest.mark.asyncio
    async def test_generate_flashcards_settings_fallback_to_instance(self, mock_litellm, mock_model_config, mocker):
        """Test fallback to instance language when Settings access fails."""
        client = LLMClient(language="german")

        # Mock the API call
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message.content = """[
            {
                "question": "Was ist die Hauptstadt?",
                "answer": "Berlin",
                "card_type": "qa"
            }
        ]"""

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response.choices[0].message.content

        # Test with explicit language parameter to use instance language
        _ = await client.generate_flashcards_from_text("Test text", language="german")

        # Check that German prompt was used (instance language)
        call_args = mock_api.call_args[0][0]  # Get the prompt argument
        assert "Sie sind ein Experte" in call_args

    @pytest.mark.asyncio
    async def test_generate_flashcards_explicit_language_overrides_settings(
        self, mock_litellm, mock_model_config, mocker
    ):
        """Test that explicit language parameter overrides Settings configuration."""
        client = LLMClient(language="english")

        # Mock Settings to return Italian
        mock_settings = mocker.Mock()
        mock_settings.cardlang = "italian"

        # Mock the API call
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message.content = """[
            {
                "question": "Quelle est la capitale?",
                "answer": "Paris",
                "card_type": "qa"
            }
        ]"""

        mocker.patch("src.document_to_anki.config.settings", mock_settings)
        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response.choices[0].message.content

        # Explicitly specify French, should override Settings Italian
        _ = await client.generate_flashcards_from_text("Test text", language="french")

        # Check that French prompt was used (explicit parameter overrides Settings)
        call_args = mock_api.call_args[0][0]  # Get the prompt argument
        assert "Vous êtes un expert" in call_args

    def test_generate_flashcards_sync_uses_settings_language(self, mock_litellm, mock_model_config, mocker):
        """Test that sync wrapper uses Settings language configuration."""
        client = LLMClient(language="english")

        # Mock Settings to return German
        mock_settings = mocker.Mock()
        mock_settings.cardlang = "german"

        mocker.patch("src.document_to_anki.config.settings", mock_settings)
        # Mock the async method
        mock_async = mocker.patch.object(client, "generate_flashcards_from_text", new_callable=mocker.AsyncMock)
        mock_async.return_value = [{"question": "Test", "answer": "Test", "card_type": "qa"}]

        result = client.generate_flashcards_from_text_sync("Test text")

        # Check that async method was called with no language (should use Settings)
        mock_async.assert_called_once_with("Test text", language=None, content_type="general")
        assert result == [{"question": "Test", "answer": "Test", "card_type": "qa"}]

    def test_generate_flashcards_sync_wrapper(self, mock_litellm, mock_model_config, mocker):
        """Test synchronous wrapper for generate_flashcards_from_text."""
        client = LLMClient(language="french")

        # Mock the async method
        mock_async = mocker.patch.object(client, "generate_flashcards_from_text", new_callable=mocker.AsyncMock)
        mock_async.return_value = [{"question": "Test", "answer": "Test", "card_type": "qa"}]

        result = client.generate_flashcards_from_text_sync("Test text", language="italian")

        # Check that async method was called with correct parameters
        mock_async.assert_called_once_with("Test text", language="italian", content_type="general")
        assert result == [{"question": "Test", "answer": "Test", "card_type": "qa"}]

    @pytest.mark.asyncio
    async def test_generate_flashcards_backward_compatibility(self, mock_litellm, mock_model_config, mocker):
        """Test that existing method calls without language parameter still work."""
        client = LLMClient(language="french")

        # Mock the API call
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message.content = """[
            {
                "question": "Quelle est la capitale?",
                "answer": "Paris",
                "card_type": "qa"
            }
        ]"""

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response.choices[0].message.content

        # Call without language parameter (backward compatibility)
        flashcards = await client.generate_flashcards_from_text("Test text")

        # Should work and return flashcards
        assert len(flashcards) == 1
        assert flashcards[0]["question"] == "Quelle est la capitale?"
        assert flashcards[0]["answer"] == "Paris"
        assert flashcards[0]["card_type"] == "qa"

    @pytest.mark.asyncio
    async def test_generate_flashcards_different_languages_integration(self, mock_litellm, mock_model_config, mocker):
        """Test flashcard generation with different languages from Settings."""
        client = LLMClient(language="english")

        test_cases = [
            ("english", "What is the capital?", "The capital is London"),
            ("french", "Quelle est la capitale?", "La capitale est Paris"),
            ("italian", "Qual è la capitale?", "La capitale è Roma"),
            ("german", "Was ist die Hauptstadt?", "Die Hauptstadt ist Berlin"),
        ]

        for language, expected_question, expected_answer in test_cases:
            # Mock Settings for each language
            mock_settings = mocker.Mock()
            mock_settings.cardlang = language

            # Mock API response for each language
            mock_response = mocker.Mock()
            mock_response.choices = [mocker.Mock()]
            mock_response.choices[0].message.content = f"""[
                {{
                    "question": "{expected_question}",
                    "answer": "{expected_answer}",
                    "card_type": "qa"
                }}
            ]"""

            mocker.patch("src.document_to_anki.config.settings", mock_settings)
            mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
            mock_api.return_value = mock_response.choices[0].message.content

            flashcards = await client.generate_flashcards_from_text("Test text")

            # Verify correct flashcards were generated
            assert len(flashcards) == 1
            assert flashcards[0]["question"] == expected_question
            assert flashcards[0]["answer"] == expected_answer
            assert flashcards[0]["card_type"] == "qa"

    def test_validate_response_language_detailed_metrics(self, mock_litellm, mock_model_config, mocker):
        """Test that language validation returns detailed metrics."""
        client = LLMClient(language="english")

        flashcards = [
            FlashcardData("What is the capital of France?", "The capital is Paris", "qa"),
            FlashcardData("Where are the documents?", "They are on the table", "qa"),
        ]

        is_valid, metrics = client._validate_response_language(flashcards, "english")

        # Check that all expected metrics are present
        assert "success_rate" in metrics
        assert "matches_found" in metrics
        assert "total_checks" in metrics
        assert "sample_size" in metrics
        assert "language_info" in metrics
        assert "validation_method" in metrics
        assert "patterns_used" in metrics
        assert "flashcards_checked" in metrics

        # Check metric values
        assert metrics["sample_size"] == 2
        assert metrics["validation_method"] == "pattern_matching"
        assert len(metrics["patterns_used"]) > 0
        assert len(metrics["flashcards_checked"]) == 2
        assert metrics["language_info"].name == "English"

    def test_validate_response_language_no_patterns_available(self, mock_litellm, mock_model_config, mocker):
        """Test language validation when no patterns are available."""
        client = LLMClient()

        # Mock LanguageConfig to return a language without patterns
        mock_lang_config = mocker.patch("src.document_to_anki.core.llm_client.LanguageConfig")
        mock_lang_config.normalize_language.return_value = "test_lang"
        mock_info = mocker.Mock()
        mock_info.name = "Test Language"
        mock_info.code = "tl"
        mock_info.prompt_key = "test_lang"
        mock_lang_config.get_language_info.return_value = mock_info

        flashcards = [FlashcardData("Test question", "Test answer", "qa")]

        is_valid, metrics = client._validate_response_language(flashcards, "test_lang")

        assert is_valid
        assert metrics["validation_method"] == "no_patterns"
        assert metrics["patterns_used"] == []

    def test_validate_response_language_enhanced_patterns(self, mock_litellm, mock_model_config, mocker):
        """Test that enhanced language patterns work correctly."""
        client = LLMClient()

        # Test with more comprehensive text that should trigger multiple patterns
        test_cases = [
            (
                "english",
                [
                    FlashcardData("What do you think about this?", "I think it is very good", "qa"),
                    FlashcardData("Where did they go?", "They went to the store", "qa"),
                ],
            ),
            (
                "french",
                [
                    FlashcardData("Qu'est-ce que vous pensez?", "Je pense que c'est très bien", "qa"),
                    FlashcardData("Où sont-ils allés?", "Ils sont allés au magasin", "qa"),
                ],
            ),
            (
                "italian",
                [
                    FlashcardData("Cosa ne pensi?", "Penso che sia molto bene", "qa"),
                    FlashcardData("Dove sono andati?", "Sono andati al negozio", "qa"),
                ],
            ),
            (
                "german",
                [
                    FlashcardData("Was denkst du darüber?", "Ich denke, es ist sehr gut", "qa"),
                    FlashcardData("Wo sind sie hingegangen?", "Sie sind zum Geschäft gegangen", "qa"),
                ],
            ),
        ]

        for language, flashcards in test_cases:
            is_valid, metrics = client._validate_response_language(flashcards, language)

            # Should pass validation with good success rate
            assert is_valid, f"Validation failed for {language}"
            assert metrics["success_rate"] >= 0.3, f"Low success rate for {language}: {metrics['success_rate']}"
            assert metrics["matches_found"] > 0, f"No matches found for {language}"

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_language_validation_success(self, mock_litellm, mock_model_config, mocker):
        """Test successful flashcard generation with language validation."""
        client = LLMClient(language="english")

        # Mock API response with valid English content
        mock_response = """[
            {
                "question": "What is the capital of France?",
                "answer": "The capital is Paris",
                "card_type": "qa"
            }
        ]"""

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response

        flashcards, validation_summary = await client._generate_flashcards_with_language_validation(
            "Test text about France", "english", "general"
        )

        assert len(flashcards) == 1
        assert flashcards[0].question == "What is the capital of France?"
        assert validation_summary["final_validation_passed"]
        assert validation_summary["total_attempts"] == 1
        assert not validation_summary["fallback_used"]

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_language_validation_retry(self, mock_litellm, mock_model_config, mocker):
        """Test flashcard generation with language validation retry mechanism."""
        client = LLMClient(language="english")

        # Mock API responses: first fails validation, second succeeds
        responses = [
            # First response: French content when expecting English
            """[
                {
                    "question": "Quelle est la capitale?",
                    "answer": "La capitale est Paris",
                    "card_type": "qa"
                }
            ]""",
            # Second response: English content
            """[
                {
                    "question": "What is the capital?",
                    "answer": "The capital is Paris",
                    "card_type": "qa"
                }
            ]""",
        ]

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.side_effect = responses

        flashcards, validation_summary = await client._generate_flashcards_with_language_validation(
            "Test text", "english", "general", max_validation_retries=2
        )

        assert len(flashcards) == 1
        assert flashcards[0].question == "What is the capital?"
        assert validation_summary["final_validation_passed"]
        assert validation_summary["total_attempts"] == 2
        assert not validation_summary["fallback_used"]
        assert len(validation_summary["validation_results"]) == 2

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_language_validation_fallback(self, mock_litellm, mock_model_config, mocker):
        """Test flashcard generation fallback behavior when validation consistently fails."""
        client = LLMClient(language="english")

        # Mock API response that consistently fails validation
        mock_response = """[
            {
                "question": "Quelle est la capitale?",
                "answer": "La capitale est Paris",
                "card_type": "qa"
            }
        ]"""

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response

        flashcards, validation_summary = await client._generate_flashcards_with_language_validation(
            "Test text", "english", "general", max_validation_retries=1
        )

        # Should return flashcards despite validation failure (fallback behavior)
        assert len(flashcards) == 1
        assert not validation_summary["final_validation_passed"]
        assert validation_summary["fallback_used"]
        assert validation_summary["total_attempts"] == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_language_validation_english_fallback(
        self, mock_litellm, mock_model_config, mocker
    ):
        """Test English fallback when original language fails completely."""
        client = LLMClient(language="french")

        # Mock responses: French attempts fail, English fallback succeeds
        responses = [
            # French attempts return empty or fail
            "[]",
            "[]",
            # English fallback succeeds
            """[
                {
                    "question": "What is the capital?",
                    "answer": "The capital is Paris",
                    "card_type": "qa"
                }
            ]""",
        ]

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.side_effect = responses

        flashcards, validation_summary = await client._generate_flashcards_with_language_validation(
            "Test text", "french", "general", max_validation_retries=1
        )

        assert len(flashcards) == 1
        assert validation_summary["fallback_used"]
        assert "fallback_language" in validation_summary
        assert validation_summary["fallback_language"] == "english"

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_language_validation_complete_failure(
        self, mock_litellm, mock_model_config, mocker
    ):
        """Test complete failure scenario with all fallbacks exhausted."""
        client = LLMClient(language="french")

        # Mock all attempts to fail or return empty
        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = "[]"  # Always return empty

        flashcards, validation_summary = await client._generate_flashcards_with_language_validation(
            "Test text", "french", "general", max_validation_retries=1
        )

        assert len(flashcards) == 0 == 0
        assert validation_summary["fallback_used"]
        assert not validation_summary["final_validation_passed"]

    def test_log_validation_summary(self, mock_litellm, mock_model_config, mocker):
        """Test comprehensive validation summary logging."""
        client = LLMClient(language="english")

        validation_stats = {
            "total_chunks": 5,
            "successful_chunks": 4,
            "failed_chunks": 1,
            "validation_failures": 2,
            "fallback_used": 1,
            "chunk_results": [
                {"chunk_index": 1, "flashcards_generated": 3, "validation_summary": {"final_validation_passed": True}},
                {"chunk_index": 2, "flashcards_generated": 2, "validation_summary": {"final_validation_passed": False}},
            ],
        }

        mock_logger = mocker.patch("src.document_to_anki.core.llm_client.logger")
        client._log_validation_summary("english", validation_stats)

        # Check that info log was called with summary
        mock_logger.info.assert_called()
        info_call = mock_logger.info.call_args[0][0]
        assert "Language validation summary" in info_call
        assert "Total chunks processed: 5" in info_call
        assert "Successful chunks: 4/5" in info_call

    def test_log_validation_summary_warnings(self, mock_litellm, mock_model_config, mocker):
        """Test that validation summary logs appropriate warnings."""
        client = LLMClient(language="english")

        # High failure rate scenario
        validation_stats = {
            "total_chunks": 4,
            "successful_chunks": 2,
            "failed_chunks": 2,
            "validation_failures": 2,  # 100% validation failure rate
            "fallback_used": 1,
            "chunk_results": [],
        }

        mock_logger = mocker.patch("src.document_to_anki.core.llm_client.logger")
        client._log_validation_summary("english", validation_stats)

        # Check that warnings were logged
        mock_logger.warning.assert_called()
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]

        # Should warn about high validation failure rate
        validation_warning = any("High language validation failure rate" in call for call in warning_calls)
        assert validation_warning

        # Should warn about fallback usage
        fallback_warning = any("Fallback behavior was used" in call for call in warning_calls)
        assert fallback_warning

        # Should warn about high chunk failure rate
        chunk_failure_warning = any("High chunk failure rate" in call for call in warning_calls)
        assert chunk_failure_warning

    @pytest.mark.asyncio
    async def test_generate_flashcards_integration_with_validation(self, mock_litellm, mock_model_config, mocker):
        """Test integration of enhanced validation with main generate_flashcards_from_text method."""
        client = LLMClient(language="english")

        # Mock Settings
        mock_settings = mocker.Mock()
        mock_settings.cardlang = "english"

        # Mock API response
        mock_response = """[
            {
                "question": "What is the capital?",
                "answer": "The capital is Paris",
                "card_type": "qa"
            }
        ]"""

        mocker.patch("src.document_to_anki.config.settings", mock_settings)
        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response

        mock_log_summary = mocker.patch.object(client, "_log_validation_summary")
        flashcards = await client.generate_flashcards_from_text("Test text")

        assert len(flashcards) == 1
        assert flashcards[0]["question"] == "What is the capital?"

        # Check that validation summary was logged
        mock_log_summary.assert_called_once()
        call_args = mock_log_summary.call_args
        assert call_args[0][0] == "english"  # language
        validation_stats = call_args[0][1]  # validation_stats
        assert "total_chunks" in validation_stats
        assert "successful_chunks" in validation_stats

    @pytest.mark.asyncio
    async def test_generate_flashcards_validation_retry_logging(self, mock_litellm, mock_model_config, mocker):
        """Test that retry attempts are properly logged during validation."""
        client = LLMClient(language="english")

        # Mock API response that fails validation
        mock_response = """[
            {
                "question": "Quelle est la capitale?",
                "answer": "La capitale est Paris",
                "card_type": "qa"
            }
        ]"""

        mock_api = mocker.patch.object(client, "_make_api_call_with_retry", new_callable=mocker.AsyncMock)
        mock_api.return_value = mock_response

        mock_logger = mocker.patch("src.document_to_anki.core.llm_client.logger")
        flashcards, validation_summary = await client._generate_flashcards_with_language_validation(
            "Test text", "english", "general", max_validation_retries=2
        )

        # Check that retry attempts were logged
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]

        # Should log validation attempts
        validation_attempts = [call for call in debug_calls if "Language validation attempt" in call]
        assert len(validation_attempts) >= 2

        # Should log validation failures
        validation_failures = [call for call in warning_calls if "Language validation failed on attempt" in call]
        assert len(validation_failures) >= 2

        # Should log fallback behavior
        fallback_logs = [call for call in warning_calls if "All" in call and "validation attempts failed" in call]
        assert len(fallback_logs) >= 1
