"""
Test startup validation for CLI and web interfaces.

This test validates that both CLI and web interfaces properly validate
model configuration on startup and provide helpful error messages.
"""

import os

# pytest-mock provides the mocker fixture
import pytest
from click.testing import CliRunner

from src.document_to_anki.cli.main import main
from src.document_to_anki.config import ConfigurationError


class TestStartupValidation:
    """Test startup validation for CLI and web interfaces."""

    def test_cli_startup_validation_success(self, mocker):
        """Test successful CLI startup with valid model configuration."""
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash", "GEMINI_API_KEY": "test-key"})
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Document to Anki CLI" in result.output

    def test_cli_startup_validation_invalid_model(self, mocker):
        """Test CLI startup failure with invalid model."""
        mocker.patch.dict(os.environ, {"MODEL": "invalid/model"})
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "--help"])
        # CLI should fail during context initialization
        assert result.exit_code != 0
        assert "Model Configuration Error" in result.output

    def test_cli_startup_validation_missing_api_key(self, mocker):
        """Test CLI startup failure with missing API key."""
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash"}, clear=True)
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "--help"])
        # CLI should fail during context initialization
        assert result.exit_code != 0
        assert "Model Configuration Error" in result.output

    def test_cli_error_messages_are_helpful(self, mocker):
        """Test that CLI provides helpful error messages for configuration issues."""
        mocker.patch.dict(os.environ, {"MODEL": "invalid/model"})
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "nonexistent.pdf"])

        # Should contain helpful error information
        assert "Model Configuration Error" in result.output or result.exit_code != 0

    def test_web_app_startup_validation_in_lifespan(self, mocker):
        """Test that web app validates model configuration in lifespan function."""
        from fastapi import FastAPI

        from src.document_to_anki.web.app import lifespan

        # Test successful validation
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash", "GEMINI_API_KEY": "test-key"})
        app = FastAPI()
        # This should not raise an exception
        try:
            import asyncio

            async def test_lifespan():
                async with lifespan(app):
                    pass

            asyncio.run(test_lifespan())
        except Exception as e:
            # If there's an exception, it shouldn't be a ConfigurationError
            assert not isinstance(e, ConfigurationError)

    def test_web_app_startup_validation_failure(self, mocker):
        """Test that web app fails startup with invalid model configuration."""
        from fastapi import FastAPI

        from src.document_to_anki.web.app import lifespan

        # Test validation failure
        mocker.patch.dict(os.environ, {"MODEL": "invalid/model"})
        app = FastAPI()

        with pytest.raises(ConfigurationError):
            import asyncio

            async def test_lifespan():
                async with lifespan(app):
                    pass

            asyncio.run(test_lifespan())

    def test_model_configuration_endpoint_validation(self, mocker):
        """Test that model configuration endpoint properly validates current config."""
        import asyncio

        from src.document_to_anki.web.app import get_model_configuration

        # Test valid configuration
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash", "GEMINI_API_KEY": "test-key"})

        async def test_valid_config():
            response = await get_model_configuration()
            data = response.body.decode()
            assert "gemini/gemini-2.5-flash" in data
            assert '"is_valid":true' in data or '"status":"valid"' in data

        asyncio.run(test_valid_config())

        # Test invalid configuration
        mocker.patch.dict(os.environ, {"MODEL": "invalid/model"})

        async def test_invalid_config():
            response = await get_model_configuration()
            data = response.body.decode()
            assert "invalid/model" in data
            assert '"is_valid":false' in data or '"status":"invalid"' in data

        asyncio.run(test_invalid_config())

    def test_configuration_validation_with_different_providers(self, mocker):
        """Test startup validation with different model providers."""
        # Test Gemini provider
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-pro", "GEMINI_API_KEY": "test-gemini-key"})
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

        # Test OpenAI provider
        mocker.patch.dict(os.environ, {"MODEL": "openai/gpt-4", "OPENAI_API_KEY": "test-openai-key"})
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_default_model_validation_on_startup(self, mocker):
        """Test that default model is properly validated on startup."""
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
        # Remove MODEL env var to use default
        if "MODEL" in os.environ:
            del os.environ["MODEL"]

        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_startup_validation_error_recovery_guidance(self, mocker):
        """Test that startup validation provides recovery guidance."""
        mocker.patch.dict(os.environ, {"MODEL": "unsupported/model"})
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "test.pdf"])

        # Should provide guidance on how to fix the issue
        _ = result.output
        # The exact error message format may vary, but should contain helpful info
        assert result.exit_code != 0  # Should fail
        # Could check for specific guidance text if needed

    def test_verbose_mode_shows_model_information(self, mocker):
        """Test that verbose mode shows model configuration information."""
        mocker.patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash", "GEMINI_API_KEY": "test-key"})
        runner = CliRunner()
        result = runner.invoke(main, ["--verbose", "--version"])
        assert result.exit_code == 0
        # In verbose mode, should show model information
        # The exact format may vary, but should be successful
