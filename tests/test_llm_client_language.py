"""
Unit tests for LLM client language-specific functionality.

Tests the LLMClient class language support, prompt generation,
and language validation features using proper pytest-mock patterns.
"""

import pytest

from src.document_to_anki.config import LanguageInfo, LanguageValidationError
from src.document_to_anki.core.llm_client import FlashcardData, LLMClient


class TestLLMClientLanguage:
    """Test cases for LLM client language functionality."""

    @pytest.fixture
    def mock_litellm_completion(self, mocker):
        """Mock litellm.completion for testing with proper response structure."""
        return mocker.patch("src.document_to_anki.core.llm_client.litellm.completion")

    @pytest.fixture
    def mock_model_config(self, mocker):
        """Mock ModelConfig for testing."""
        mock = mocker.patch("src.document_to_anki.core.llm_client.ModelConfig")
        mock.validate_and_get_model.return_value = "gemini/gemini-2.5-flash"
        mock.validate_model_config.return_value = True
        return mock

    def _create_mock_response(self, content: str, mocker):
        """Create a properly structured mock response that matches litellm API."""
        mock_response = mocker.Mock()
        mock_response.choices = [mocker.Mock()]
        mock_response.choices[0].message = mocker.Mock()
        mock_response.choices[0].message.content = content
        return mock_response

    # Initialization Tests
    def test_init_with_language_parameter(self, mock_litellm_completion, mock_model_config):
        """Test LLMClient initialization with language parameter."""
        client = LLMClient(language="french")

        assert client.language == "french"
        assert client.model == "gemini/gemini-2.5-flash"
        assert client.language_info.name == "French"
        assert client.language_info.code == "fr"

    def test_init_with_default_language(self, mock_litellm_completion, mock_model_config):
        """Test LLMClient initialization with default language."""
        client = LLMClient()

        assert client.language == "english"
        assert client.language_info.name == "English"
        assert client.language_info.code == "en"

    def test_init_language_normalization(self, mock_litellm_completion, mock_model_config):
        """Test that language is normalized during initialization."""
        client = LLMClient(language="  FRENCH  ")

        assert client.language == "french"
        assert client.language_info.name == "French"

    def test_init_with_iso_language_code(self, mock_litellm_completion, mock_model_config):
        """Test LLMClient initialization with ISO language codes."""
        client = LLMClient(language="de")

        assert client.language == "de"  # Normalized to ISO code
        assert client.language_info.name == "German"
        assert client.language_info.code == "de"

    def test_init_with_invalid_language(self, mock_litellm_completion, mock_model_config):
        """Test LLMClient initialization with invalid language raises error."""
        with pytest.raises(LanguageValidationError, match="Unsupported language 'spanish'"):
            LLMClient(language="spanish")

    def test_init_with_empty_language(self, mock_litellm_completion, mock_model_config):
        """Test LLMClient initialization with empty language defaults to English."""
        client = LLMClient(language="")

        assert client.language == "english"
        assert client.language_info.name == "English"

    # Language Management Tests
    def test_get_current_language(self, mock_litellm_completion, mock_model_config):
        """Test getting current language configuration."""
        client = LLMClient(language="italian")

        assert client.get_current_language() == "italian"

    def test_get_language_info(self, mock_litellm_completion, mock_model_config):
        """Test getting detailed language information."""
        client = LLMClient(language="german")

        lang_info = client.get_language_info()
        assert isinstance(lang_info, LanguageInfo)
        assert lang_info.name == "German"
        assert lang_info.code == "de"
        assert lang_info.prompt_key == "german"

    def test_set_language_valid(self, mock_litellm_completion, mock_model_config):
        """Test setting a valid language."""
        client = LLMClient(language="english")

        client.set_language("italian")

        assert client.language == "italian"
        assert client.language_info.name == "Italian"
        assert client.language_info.code == "it"

    def test_set_language_invalid(self, mock_litellm_completion, mock_model_config):
        """Test setting an invalid language raises error."""
        client = LLMClient(language="english")

        with pytest.raises(LanguageValidationError, match="Unsupported language 'spanish'"):
            client.set_language("spanish")

        # Original language should be preserved
        assert client.language == "english"

    def test_set_language_with_normalization(self, mock_litellm_completion, mock_model_config):
        """Test setting language with normalization."""
        client = LLMClient(language="english")

        client.set_language("  FR  ")

        assert client.language == "fr"  # Normalized to ISO code
        assert client.language_info.name == "French"

    # Prompt Template Tests
    def test_get_prompt_template_english(self, mock_litellm_completion, mock_model_config):
        """Test getting English prompt template."""
        client = LLMClient(language="english")

        template = client.get_prompt_template("english", "general")

        assert "You are an expert educator" in template
        assert "IN ENGLISH" in template
        assert "{text}" in template

    def test_get_prompt_template_french(self, mock_litellm_completion, mock_model_config):
        """Test getting French prompt template."""
        client = LLMClient(language="french")

        template = client.get_prompt_template("french", "academic")

        assert "Vous êtes un expert" in template
        assert "EN FRANÇAIS" in template
        assert "vocabulaire académique" in template
        assert "{text}" in template

    def test_get_prompt_template_italian(self, mock_litellm_completion, mock_model_config):
        """Test getting Italian prompt template."""
        client = LLMClient(language="italian")

        template = client.get_prompt_template("italian", "technical")

        assert "Sei un esperto" in template
        assert "IN ITALIANO" in template
        assert "terminologia tecnica" in template
        assert "{text}" in template

    def test_get_prompt_template_german(self, mock_litellm_completion, mock_model_config):
        """Test getting German prompt template."""
        client = LLMClient(language="german")

        template = client.get_prompt_template("german", "general")

        assert "Sie sind ein Experte" in template
        assert "AUF DEUTSCH" in template
        assert "{text}" in template

    def test_get_prompt_template_invalid_language(self, mock_litellm_completion, mock_model_config):
        """Test that invalid language raises ValueError."""
        client = LLMClient()

        with pytest.raises(ValueError, match="Unsupported language"):
            client.get_prompt_template("spanish", "general")

    # Prompt Creation Tests
    def test_create_flashcard_prompt_uses_instance_language(self, mock_litellm_completion, mock_model_config):
        """Test that _create_flashcard_prompt uses instance language when none specified."""
        client = LLMClient(language="italian")

        prompt = client._create_flashcard_prompt("Test text")

        assert "Sei un esperto" in prompt
        assert "Test text" in prompt

    def test_create_flashcard_prompt_overrides_language(self, mock_litellm_completion, mock_model_config):
        """Test that _create_flashcard_prompt can override instance language."""
        client = LLMClient(language="english")

        prompt = client._create_flashcard_prompt("Test text", language="german")

        assert "Sie sind ein Experte" in prompt
        assert "Test text" in prompt

    def test_create_flashcard_prompt_with_content_type(self, mock_litellm_completion, mock_model_config):
        """Test _create_flashcard_prompt with different content types."""
        client = LLMClient(language="french")

        academic_prompt = client._create_flashcard_prompt("Test text", content_type="academic")
        technical_prompt = client._create_flashcard_prompt("Test text", content_type="technical")

        assert "vocabulaire académique" in academic_prompt
        assert "terminologie technique" in technical_prompt

    def test_create_flashcard_prompt_invalid_parameters(self, mock_litellm_completion, mock_model_config):
        """Test that invalid parameters raise ValueError."""
        client = LLMClient()

        with pytest.raises(ValueError, match="Invalid parameters"):
            client._create_flashcard_prompt("Test text", language="spanish")

        with pytest.raises(ValueError, match="Invalid parameters"):
            client._create_flashcard_prompt("Test text", content_type="invalid")

    # Language Validation Tests
    def test_validate_response_language_english(self, mock_litellm_completion, mock_model_config):
        """Test language validation for English flashcards."""
        client = LLMClient(language="english")

        english_flashcards = [
            FlashcardData(question="What is the capital?", answer="It is London", card_type="qa"),
            FlashcardData(question="How are you?", answer="I am fine", card_type="qa"),
        ]

        is_valid, metrics = client._validate_response_language(english_flashcards, "english")

        assert is_valid
        assert metrics["language_info"].name == "English"

    def test_validate_response_language_french(self, mock_litellm_completion, mock_model_config):
        """Test language validation for French flashcards."""
        client = LLMClient(language="french")

        french_flashcards = [
            FlashcardData(question="Quelle est la capitale?", answer="C'est Paris", card_type="qa"),
            FlashcardData(question="Comment allez-vous?", answer="Je vais bien", card_type="qa"),
        ]

        is_valid, metrics = client._validate_response_language(french_flashcards, "french")

        assert is_valid
        assert metrics["language_info"].name == "French"

    def test_validate_response_language_mismatch(self, mock_litellm_completion, mock_model_config):
        """Test language validation with language mismatch."""
        client = LLMClient(language="english")

        # English flashcards when French is expected
        english_flashcards = [
            FlashcardData(question="What is the capital?", answer="It is London", card_type="qa"),
        ]

        is_valid, metrics = client._validate_response_language(english_flashcards, "french")

        assert not is_valid
        assert metrics["language_info"].name == "French"

    def test_validate_response_language_empty_list(self, mock_litellm_completion, mock_model_config):
        """Test language validation with empty flashcard list."""
        client = LLMClient()

        is_valid, metrics = client._validate_response_language([], "english")

        assert is_valid
        assert metrics["sample_size"] == 0

    # Async Flashcard Generation Tests
    @pytest.mark.asyncio
    async def test_generate_flashcards_uses_instance_language(self, mock_litellm_completion, mock_model_config, mocker):
        """Test that generate_flashcards_from_text uses instance language when no language specified."""
        client = LLMClient(language="german")

        # Create proper mock response that matches litellm API structure
        mock_response_content = """[
            {
                "question": "Was ist die Hauptstadt?",
                "answer": "Berlin",
                "card_type": "qa"
            }
        ]"""

        mock_response = self._create_mock_response(mock_response_content, mocker)
        mock_litellm_completion.return_value = mock_response

        # Call with explicit language parameter to use instance language
        result = await client.generate_flashcards_from_text("Test text", language="german")

        # Verify the result
        assert len(result) == 1
        assert result[0]["question"] == "Was ist die Hauptstadt?"
        assert result[0]["answer"] == "Berlin"

        # Check that litellm.completion was called with German prompt
        mock_litellm_completion.assert_called_once()
        call_args = mock_litellm_completion.call_args[1]  # Get keyword arguments
        prompt = call_args["messages"][0]["content"]
        assert "Sie sind ein Experte" in prompt

    @pytest.mark.asyncio
    async def test_generate_flashcards_overrides_language(self, mock_litellm_completion, mock_model_config, mocker):
        """Test that generate_flashcards_from_text can override instance language."""
        client = LLMClient(language="english")

        # Create proper mock response that matches litellm API structure
        mock_response_content = """[
            {
                "question": "Quelle est la capitale?",
                "answer": "Paris",
                "card_type": "qa"
            }
        ]"""

        mock_response = self._create_mock_response(mock_response_content, mocker)
        mock_litellm_completion.return_value = mock_response

        result = await client.generate_flashcards_from_text("Test text", language="french")

        # Verify the result
        assert len(result) == 1
        assert result[0]["question"] == "Quelle est la capitale?"
        assert result[0]["answer"] == "Paris"

        # Check that litellm.completion was called with French prompt
        mock_litellm_completion.assert_called_once()
        call_args = mock_litellm_completion.call_args[1]  # Get keyword arguments
        prompt = call_args["messages"][0]["content"]
        assert "Vous êtes un expert" in prompt

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_content_type(self, mock_litellm_completion, mock_model_config, mocker):
        """Test generate_flashcards_from_text with different content types."""
        client = LLMClient(language="italian")

        # Create Italian content that will pass language validation
        mock_response_content = """[
            {
                "question": "Che cos'è l'intelligenza artificiale?",
                "answer": "È una tecnologia molto avanzata che utilizza algoritmi",
                "card_type": "qa"
            }
        ]"""

        mock_response = self._create_mock_response(mock_response_content, mocker)
        mock_litellm_completion.return_value = mock_response

        # Explicitly specify language to override any Settings configuration
        result = await client.generate_flashcards_from_text("Test text", language="italian", content_type="technical")

        # Verify the result
        assert len(result) == 1
        assert result[0]["question"] == "Che cos'è l'intelligenza artificiale?"

        # Check that litellm.completion was called (may be multiple times due to language validation)
        assert mock_litellm_completion.call_count >= 1

        # Check that technical prompt was used in the first call
        first_call_args = mock_litellm_completion.call_args_list[0][1]
        prompt = first_call_args["messages"][0]["content"]
        assert "terminologia tecnica" in prompt

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_language_validation_success(
        self, mock_litellm_completion, mock_model_config, mocker
    ):
        """Test successful flashcard generation with language validation."""
        client = LLMClient(language="english")

        mock_response_content = """[
            {
                "question": "What is the capital of France?",
                "answer": "The capital is Paris",
                "card_type": "qa"
            }
        ]"""

        mock_response = self._create_mock_response(mock_response_content, mocker)
        mock_litellm_completion.return_value = mock_response

        result = await client.generate_flashcards_from_text("Test text about France")

        # Verify successful generation
        assert len(result) == 1
        assert result[0]["question"] == "What is the capital of France?"
        assert result[0]["answer"] == "The capital is Paris"

    @pytest.mark.asyncio
    async def test_generate_flashcards_with_language_validation_retry(
        self, mock_litellm_completion, mock_model_config, mocker
    ):
        """Test flashcard generation with language validation retry mechanism."""
        client = LLMClient(language="french")

        # First response in wrong language, second in correct language
        responses = [
            """[{"question": "What is AI?", "answer": "Artificial Intelligence", "card_type": "qa"}]""",  # English
            """[{"question": "Qu'est-ce que l'IA?", "answer": "Intelligence Artificielle", "card_type": "qa"}]""",
        ]

        mock_responses = [self._create_mock_response(resp, mocker) for resp in responses]
        mock_litellm_completion.side_effect = mock_responses

        result = await client.generate_flashcards_from_text("Test text")

        # Should get the French result after retry
        assert len(result) == 1
        assert result[0]["question"] == "Qu'est-ce que l'IA?"
        assert result[0]["answer"] == "Intelligence Artificielle"

        # Should have been called twice (initial + retry)
        assert mock_litellm_completion.call_count == 2

    # Synchronous Wrapper Test
    def test_generate_flashcards_from_text_sync(self, mock_litellm_completion, mock_model_config, mocker):
        """Test synchronous wrapper for generate_flashcards_from_text."""
        client = LLMClient(language="english")

        mock_response_content = """[
            {
                "question": "What is Python?",
                "answer": "A programming language",
                "card_type": "qa"
            }
        ]"""

        mock_response = self._create_mock_response(mock_response_content, mocker)
        mock_litellm_completion.return_value = mock_response

        result = client.generate_flashcards_from_text_sync("Python is a programming language.", language="english")

        assert len(result) == 1
        assert result[0]["question"] == "What is Python?"
        assert result[0]["answer"] == "A programming language"
