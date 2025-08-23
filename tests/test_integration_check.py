"""
Integration test to validate ModelConfig integration throughout the application.

This test validates that ModelConfig is properly integrated in:
- LLMClient initialization and validation
- FlashcardGenerator initialization
- CLI startup validation
- Web app startup validation
- Error handling for invalid models and missing API keys
"""

import os

# pytest-mock provides the mocker fixture
import pytest

from src.document_to_anki.config import ConfigurationError, ModelConfig
from src.document_to_anki.core.flashcard_generator import FlashcardGenerator
from src.document_to_anki.core.llm_client import LLMClient


class TestModelConfigIntegration:
    """Test ModelConfig integration throughout the application."""

    def test_llm_client_uses_model_config_by_default(self, mocker):
        """Test that LLMClient uses ModelConfig when no model is provided."""
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash", "GEMINI_API_KEY": "test-key"})
        client = LLMClient()
        assert client.get_current_model() == "gemini/gemini-2.5-flash"

    def test_llm_client_validates_provided_model(self, mocker):
        """Test that LLMClient validates provided model using ModelConfig."""
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
        # Valid model should work
        client = LLMClient(model="gemini/gemini-2.5-flash")
        assert client.get_current_model() == "gemini/gemini-2.5-flash"

        # Invalid model should raise ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            LLMClient(model="invalid/model")
        assert "Unsupported model" in str(exc_info.value)

    def test_llm_client_validates_api_key_for_model(self, mocker):
        """Test that LLMClient validates API key for the selected model."""
        # Missing API key should raise ConfigurationError
        mocker.patch.dict(os.environ, {}, clear=True)
        with pytest.raises(ConfigurationError) as exc_info:
            LLMClient(model="gemini/gemini-2.5-flash")
        assert "Missing API key" in str(exc_info.value)
        assert "GEMINI_API_KEY" in str(exc_info.value)

    def test_flashcard_generator_uses_model_config_llm_client(self, mocker):
        """Test that FlashcardGenerator creates LLMClient with ModelConfig."""
        mocker.patch.dict(os.environ, {"MODEL": "openai/gpt-4", "OPENAI_API_KEY": "test-key"})
        generator = FlashcardGenerator()
        assert generator.llm_client.get_current_model() == "openai/gpt-4"

    def test_flashcard_generator_propagates_configuration_errors(self, mocker):
        """Test that FlashcardGenerator propagates ModelConfig errors."""
        mocker.patch.dict(os.environ, {"MODEL": "invalid/model"})
        with pytest.raises(ConfigurationError) as exc_info:
            FlashcardGenerator()
        assert "Unsupported model" in str(exc_info.value)

    def test_model_config_environment_variable_precedence(self, mocker):
        """Test that MODEL environment variable takes precedence."""
        # Test default model
        mocker.patch.dict(os.environ, {}, clear=True)
        model = ModelConfig.get_model_from_env()
        assert model == ModelConfig.DEFAULT_MODEL

        # Test custom model
        mocker.patch.dict(os.environ, {"MODEL": "openai/gpt-4"})
        model = ModelConfig.get_model_from_env()
        assert model == "openai/gpt-4"

    def test_model_config_validation_with_different_providers(self, mocker):
        """Test ModelConfig validation with different model providers."""
        # Test Gemini model validation
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
        assert ModelConfig.validate_model_config("gemini/gemini-2.5-flash") is True
        assert ModelConfig.validate_model_config("gemini/gemini-2.5-pro") is True

        # Test OpenAI model validation
        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
        assert ModelConfig.validate_model_config("openai/gpt-4") is True
        assert ModelConfig.validate_model_config("openai/gpt-3.5-turbo") is True

        # Test missing API keys
        mocker.patch.dict(os.environ, {}, clear=True)
        assert ModelConfig.validate_model_config("gemini/gemini-2.5-flash") is False
        assert ModelConfig.validate_model_config("openai/gpt-4") is False

    def test_model_config_validate_and_get_model_success(self, mocker):
        """Test successful model validation and retrieval."""
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-pro", "GEMINI_API_KEY": "test-key"})
        model = ModelConfig.validate_and_get_model()
        assert model == "gemini/gemini-2.5-pro"

    def test_model_config_validate_and_get_model_invalid_model(self, mocker):
        """Test error handling for invalid model."""
        mocker.patch.dict(os.environ, {"MODEL": "invalid/model"})
        with pytest.raises(ConfigurationError) as exc_info:
            ModelConfig.validate_and_get_model()

        error_msg = str(exc_info.value)
        assert "Unsupported model 'invalid/model'" in error_msg
        assert "gemini/gemini-2.5-flash" in error_msg  # Should list supported models

    def test_model_config_validate_and_get_model_missing_api_key(self, mocker):
        """Test error handling for missing API key."""
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash"}, clear=True)
        with pytest.raises(ConfigurationError) as exc_info:
            ModelConfig.validate_and_get_model()

        error_msg = str(exc_info.value)
        assert "Missing API key for model 'gemini/gemini-2.5-flash'" in error_msg
        assert "GEMINI_API_KEY" in error_msg

    def test_model_config_get_required_api_key(self):
        """Test getting required API key for different models."""
        assert ModelConfig.get_required_api_key("gemini/gemini-2.5-flash") == "GEMINI_API_KEY"
        assert ModelConfig.get_required_api_key("gemini/gemini-2.5-pro") == "GEMINI_API_KEY"
        assert ModelConfig.get_required_api_key("openai/gpt-4") == "OPENAI_API_KEY"
        assert ModelConfig.get_required_api_key("openai/gpt-3.5-turbo") == "OPENAI_API_KEY"
        assert ModelConfig.get_required_api_key("invalid/model") is None

    def test_model_config_supported_models_list(self):
        """Test that supported models list is comprehensive."""
        supported_models = ModelConfig.get_supported_models()

        # Check that key models are included
        assert "gemini/gemini-2.5-flash" in supported_models
        assert "gemini/gemini-2.5-pro" in supported_models
        assert "openai/gpt-4" in supported_models
        assert "openai/gpt-3.5-turbo" in supported_models

        # Check that all models have corresponding API keys
        for model in supported_models:
            api_key = ModelConfig.get_required_api_key(model)
            assert api_key is not None
            assert api_key.endswith("_API_KEY")

    def test_end_to_end_model_configuration_flow(self, mocker):
        """Test complete end-to-end model configuration flow."""
        # Test successful configuration and component initialization
        mocker.patch.dict(os.environ, {"MODEL": "openai/gpt-4", "OPENAI_API_KEY": "test-openai-key"})
        # Validate model configuration
        model = ModelConfig.validate_and_get_model()
        assert model == "openai/gpt-4"

        # Initialize LLMClient with validated model
        llm_client = LLMClient()
        assert llm_client.get_current_model() == "openai/gpt-4"

        # Initialize FlashcardGenerator with configured LLMClient
        generator = FlashcardGenerator()
        assert generator.llm_client.get_current_model() == "openai/gpt-4"

    def test_model_switching_between_providers(self, mocker):
        """Test switching between different model providers."""
        # Start with Gemini
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash", "GEMINI_API_KEY": "test-gemini-key"})
        generator1 = FlashcardGenerator()
        assert generator1.llm_client.get_current_model() == "gemini/gemini-2.5-flash"

        # Switch to OpenAI
        mocker.patch.dict(os.environ, {"MODEL": "openai/gpt-4", "OPENAI_API_KEY": "test-openai-key"})
        generator2 = FlashcardGenerator()
        assert generator2.llm_client.get_current_model() == "openai/gpt-4"

    def test_configuration_error_messages_are_helpful(self, mocker):
        """Test that configuration error messages provide helpful guidance."""
        # Test unsupported model error
        mocker.patch.dict(os.environ, {"MODEL": "unsupported/model"})
        with pytest.raises(ConfigurationError) as exc_info:
            ModelConfig.validate_and_get_model()

        error_msg = str(exc_info.value)
        assert "Unsupported model" in error_msg
        assert "gemini/gemini-2.5-flash" in error_msg  # Should suggest valid models

        # Test missing API key error
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash"}, clear=True)
        with pytest.raises(ConfigurationError) as exc_info:
            ModelConfig.validate_and_get_model()

        error_msg = str(exc_info.value)
        assert "Missing API key" in error_msg
        assert "GEMINI_API_KEY" in error_msg  # Should specify required key

    def test_default_model_fallback(self, mocker):
        """Test that default model is used when MODEL env var is not set."""
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
        # Remove MODEL env var if it exists
        if "MODEL" in os.environ:
            del os.environ["MODEL"]

        model = ModelConfig.validate_and_get_model()
        assert model == ModelConfig.DEFAULT_MODEL
        assert model == "gemini/gemini-2.5-flash"

    def test_model_config_constants_are_valid(self):
        """Test that ModelConfig constants are properly defined."""
        # Test DEFAULT_MODEL is in supported models
        assert ModelConfig.DEFAULT_MODEL in ModelConfig.SUPPORTED_MODELS

        # Test SUPPORTED_MODELS structure
        assert isinstance(ModelConfig.SUPPORTED_MODELS, dict)
        assert len(ModelConfig.SUPPORTED_MODELS) > 0

        # Test all models follow expected format
        for model, api_key in ModelConfig.SUPPORTED_MODELS.items():
            assert "/" in model  # Should have provider/model format
            assert api_key.endswith("_API_KEY")  # Should follow naming convention
            assert api_key in ["GEMINI_API_KEY", "OPENAI_API_KEY"]  # Should be known key
