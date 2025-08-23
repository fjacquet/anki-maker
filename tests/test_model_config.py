"""Tests for ModelConfig class."""

import os
from unittest.mock import patch

import pytest

from src.document_to_anki.config import ConfigurationError, ModelConfig


class TestModelConfig:
    """Test cases for ModelConfig class."""
    
    def test_get_model_from_env_with_env_var(self):
        """Test getting model from environment variable."""
        with patch.dict(os.environ, {"MODEL": "openai/gpt-4"}):
            model = ModelConfig.get_model_from_env()
            assert model == "openai/gpt-4"
    
    def test_get_model_from_env_default(self):
        """Test getting default model when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            model = ModelConfig.get_model_from_env()
            assert model == ModelConfig.DEFAULT_MODEL
            assert model == "gemini/gemini-2.5-flash"
    
    def test_get_supported_models(self):
        """Test getting list of supported models."""
        models = ModelConfig.get_supported_models()
        expected_models = [
            "gemini/gemini-2.5-flash",
            "gemini/gemini-2.5-pro",
            "openai/gpt-4", 
            "openai/gpt-3.5-turbo",
            "openai/gpt-4.1",
            "openai/gpt-4.1-mini",
            "openai/gpt-4.1-nano",
            "openai/gpt-5",
            "openai/gpt-5-mini",
            "openai/gpt-5-nano",
            "openai/gpt-4o"
        ]
        assert set(models) == set(expected_models)
        assert len(models) == 11
    
    def test_validate_model_config_valid_with_api_key(self):
        """Test validation with valid model and API key."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            result = ModelConfig.validate_model_config("gemini/gemini-2.5-flash")
            assert result is True
    
    def test_validate_model_config_valid_without_api_key(self):
        """Test validation with valid model but missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = ModelConfig.validate_model_config("gemini/gemini-2.5-flash")
            assert result is False
    
    def test_validate_model_config_invalid_model(self):
        """Test validation with invalid model."""
        result = ModelConfig.validate_model_config("invalid/model")
        assert result is False
    
    def test_get_required_api_key_valid_model(self):
        """Test getting required API key for valid model."""
        api_key = ModelConfig.get_required_api_key("gemini/gemini-2.5-flash")
        assert api_key == "GEMINI_API_KEY"
        
        api_key = ModelConfig.get_required_api_key("openai/gpt-4")
        assert api_key == "OPENAI_API_KEY"
    
    def test_get_required_api_key_invalid_model(self):
        """Test getting required API key for invalid model."""
        api_key = ModelConfig.get_required_api_key("invalid/model")
        assert api_key is None
    
    def test_validate_and_get_model_success(self):
        """Test successful model validation and retrieval."""
        with patch.dict(os.environ, {
            "MODEL": "gemini/gemini-2.5-flash",
            "GEMINI_API_KEY": "test-key"
        }):
            model = ModelConfig.validate_and_get_model()
            assert model == "gemini/gemini-2.5-flash"
    
    def test_validate_and_get_model_unsupported_model(self):
        """Test validation failure with unsupported model."""
        with patch.dict(os.environ, {"MODEL": "invalid/model"}):
            with pytest.raises(ConfigurationError) as exc_info:
                ModelConfig.validate_and_get_model()
            
            error_msg = str(exc_info.value)
            assert "Unsupported model 'invalid/model'" in error_msg
            assert "gemini/gemini-2.5-flash" in error_msg
            assert "openai/gpt-4" in error_msg
    
    def test_validate_and_get_model_missing_api_key(self):
        """Test validation failure with missing API key."""
        with patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash"}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                ModelConfig.validate_and_get_model()
            
            error_msg = str(exc_info.value)
            assert "Missing API key for model 'gemini/gemini-2.5-flash'" in error_msg
            assert "GEMINI_API_KEY" in error_msg
    
    def test_validate_and_get_model_default_with_api_key(self):
        """Test validation with default model and API key."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
            # Clear MODEL env var to use default
            if "MODEL" in os.environ:
                del os.environ["MODEL"]
            
            model = ModelConfig.validate_and_get_model()
            assert model == "gemini/gemini-2.5-flash"
    
    def test_openai_model_validation(self):
        """Test validation for OpenAI models."""
        with patch.dict(os.environ, {
            "MODEL": "openai/gpt-4",
            "OPENAI_API_KEY": "test-openai-key"
        }):
            model = ModelConfig.validate_and_get_model()
            assert model == "openai/gpt-4"
    
    def test_supported_models_constant(self):
        """Test that SUPPORTED_MODELS constant has expected structure."""
        assert isinstance(ModelConfig.SUPPORTED_MODELS, dict)
        
        # Check that all values are valid environment variable names
        for model, api_key in ModelConfig.SUPPORTED_MODELS.items():
            assert "/" in model  # Model should have provider/model format
            assert api_key.endswith("_API_KEY")  # API key should follow naming convention
    
    def test_default_model_constant(self):
        """Test that DEFAULT_MODEL is in supported models."""
        assert ModelConfig.DEFAULT_MODEL in ModelConfig.SUPPORTED_MODELS
        assert ModelConfig.DEFAULT_MODEL == "gemini/gemini-2.5-flash"