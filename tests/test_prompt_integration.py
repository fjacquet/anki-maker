"""
Integration tests for prompt template functionality with LLM client.

Tests the integration between PromptTemplates and LLMClient to ensure
proper prompt generation and language-specific functionality.
"""

# pytest-mock provides the mocker fixture

import pytest

from src.document_to_anki.core.llm_client import LLMClient
from src.document_to_anki.core.prompt_templates import PromptTemplates


class TestPromptIntegration:
    """Integration tests for prompt templates with LLM client."""

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

    def test_llm_client_uses_prompt_templates(self, mock_litellm, mock_model_config):
        """Test that LLM client properly uses PromptTemplates."""
        client = LLMClient(language="french")

        # Test that the client can get templates for all supported languages
        for lang in ["english", "french", "italian", "german"]:
            template = client.get_prompt_template(lang, "general")
            assert template is not None
            assert len(template) > 0
            assert "{text}" in template

    def test_prompt_consistency_across_languages(self, mock_litellm, mock_model_config):
        """Test that all language templates have consistent structure."""
        client = LLMClient()

        languages = ["english", "french", "italian", "german"]
        content_types = ["academic", "technical", "general"]

        for lang in languages:
            for content_type in content_types:
                template = client.get_prompt_template(lang, content_type)

                # All templates should have these essential elements
                assert "question" in template
                assert "answer" in template
                assert "card_type" in template
                assert "{text}" in template
                assert "JSON" in template.upper()

    def test_language_specific_content_in_templates(self, mock_litellm, mock_model_config):
        """Test that templates contain language-specific content."""
        client = LLMClient()

        # Test English template
        en_template = client.get_prompt_template("english", "general")
        assert "You are an expert" in en_template
        assert "IN ENGLISH" in en_template

        # Test French template
        fr_template = client.get_prompt_template("french", "general")
        assert "Vous êtes un expert" in fr_template
        assert "EN FRANÇAIS" in fr_template

        # Test Italian template
        it_template = client.get_prompt_template("italian", "general")
        assert "Sei un esperto" in it_template
        assert "IN ITALIANO" in it_template

        # Test German template
        de_template = client.get_prompt_template("german", "general")
        assert "Sie sind ein Experte" in de_template
        assert "AUF DEUTSCH" in de_template

    def test_content_type_specialization(self, mock_litellm, mock_model_config):
        """Test that content types produce specialized templates."""
        client = LLMClient()

        # Test English content type variations
        academic = client.get_prompt_template("english", "academic")
        technical = client.get_prompt_template("english", "technical")
        general = client.get_prompt_template("english", "general")

        # Academic should have academic-specific terms
        assert "academic" in academic.lower()
        assert "scientific" in academic.lower()

        # Technical should have technical-specific terms
        assert "technical" in technical.lower()
        assert "processes" in technical.lower()

        # All should be different
        assert academic != technical != general

    def test_prompt_creation_with_text_substitution(self, mock_litellm, mock_model_config):
        """Test that _create_flashcard_prompt properly substitutes text."""
        client = LLMClient(language="italian")

        test_text = "This is a test document about Italian history."
        prompt = client._create_flashcard_prompt(test_text)

        # Should contain the test text
        assert test_text in prompt
        # Should be Italian template
        assert "Sei un esperto" in prompt
        # Should not contain the placeholder
        assert "{text}" not in prompt

    def test_prompt_creation_with_different_languages(self, mock_litellm, mock_model_config):
        """Test prompt creation with different language overrides."""
        client = LLMClient(language="english")  # Default to English

        test_text = "Sample text for testing."

        # Test with different language overrides
        en_prompt = client._create_flashcard_prompt(test_text, language="english")
        fr_prompt = client._create_flashcard_prompt(test_text, language="french")
        it_prompt = client._create_flashcard_prompt(test_text, language="italian")
        de_prompt = client._create_flashcard_prompt(test_text, language="german")

        # All should contain the test text
        for prompt in [en_prompt, fr_prompt, it_prompt, de_prompt]:
            assert test_text in prompt
            assert "{text}" not in prompt

        # Should have language-specific content
        assert "You are an expert" in en_prompt
        assert "Vous êtes un expert" in fr_prompt
        assert "Sei un esperto" in it_prompt
        assert "Sie sind ein Experte" in de_prompt

    def test_prompt_creation_with_content_types(self, mock_litellm, mock_model_config):
        """Test prompt creation with different content types."""
        client = LLMClient(language="german")

        test_text = "Technical documentation about software engineering."

        academic_prompt = client._create_flashcard_prompt(test_text, content_type="academic")
        technical_prompt = client._create_flashcard_prompt(test_text, content_type="technical")
        general_prompt = client._create_flashcard_prompt(test_text, content_type="general")

        # All should contain the test text and be in German
        for prompt in [academic_prompt, technical_prompt, general_prompt]:
            assert test_text in prompt
            assert "Sie sind ein Experte" in prompt
            assert "{text}" not in prompt

        # Should have content-type specific terms
        assert "akademisches" in academic_prompt.lower()
        assert "technische" in technical_prompt.lower()

    def test_error_handling_for_invalid_parameters(self, mock_litellm, mock_model_config):
        """Test error handling for invalid language or content type parameters."""
        client = LLMClient()

        # Invalid language should raise ValueError
        with pytest.raises(ValueError, match="Invalid parameters"):
            client._create_flashcard_prompt("test", language="spanish")

        # Invalid content type should raise ValueError
        with pytest.raises(ValueError, match="Invalid parameters"):
            client._create_flashcard_prompt("test", content_type="invalid")

    def test_template_validation_integration(self, mock_litellm, mock_model_config):
        """Test that template validation works with LLM client."""
        _ = LLMClient()

        # Valid parameters should work
        assert PromptTemplates.validate_template_parameters("english", "general")
        assert PromptTemplates.validate_template_parameters("fr", "technical")

        # Invalid parameters should fail
        assert not PromptTemplates.validate_template_parameters("spanish", "general")
        assert not PromptTemplates.validate_template_parameters("english", "invalid")

    def test_iso_code_support_in_integration(self, mock_litellm, mock_model_config):
        """Test that ISO language codes work properly in integration."""
        client = LLMClient()

        # Test that ISO codes produce same results as full names
        en_full = client.get_prompt_template("english", "general")
        en_iso = client.get_prompt_template("en", "general")
        assert en_full == en_iso

        fr_full = client.get_prompt_template("french", "academic")
        fr_iso = client.get_prompt_template("fr", "academic")
        assert fr_full == fr_iso

        it_full = client.get_prompt_template("italian", "technical")
        it_iso = client.get_prompt_template("it", "technical")
        assert it_full == it_iso

        de_full = client.get_prompt_template("german", "general")
        de_iso = client.get_prompt_template("de", "general")
        assert de_full == de_iso
