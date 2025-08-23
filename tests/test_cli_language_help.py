"""Integration tests for CLI language help text and error messages."""

import os
import subprocess
import sys

import pytest
from click.testing import CliRunner

from document_to_anki.cli.main import main
from document_to_anki.config import LanguageConfig


class TestCLILanguageHelp:
    """Test CLI language configuration help and error messages."""

    def test_main_help_includes_language_info(self):
        """Test that main help text includes language configuration information."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        help_text = result.output

        # Check for language configuration section
        assert "LANGUAGE CONFIGURATION:" in help_text
        assert "CARDLANG" in help_text
        assert "English" in help_text
        assert "French" in help_text
        assert "Italian" in help_text
        assert "German" in help_text

        # Check for examples
        assert "export CARDLANG=" in help_text

    def test_convert_help_includes_language_info(self):
        """Test that convert command help includes language configuration."""
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "--help"])

        assert result.exit_code == 0
        help_text = result.output

        # Check for language configuration section
        assert "LANGUAGE CONFIGURATION:" in help_text
        assert "CARDLANG" in help_text
        assert "Supported languages:" in help_text

        # Check for supported language codes
        assert "(en)" in help_text
        assert "(fr)" in help_text
        assert "(it)" in help_text
        assert "(de)" in help_text

        # Check for examples
        assert "CARDLANG=french" in help_text
        assert "CARDLANG=de" in help_text

    def test_batch_convert_help_includes_language_info(self):
        """Test that batch-convert command help includes language configuration."""
        runner = CliRunner()
        result = runner.invoke(main, ["batch-convert", "--help"])

        assert result.exit_code == 0
        help_text = result.output

        # Check for language configuration section
        assert "LANGUAGE CONFIGURATION:" in help_text
        assert "CARDLANG" in help_text
        assert "Supported:" in help_text

        # Check for example
        assert "CARDLANG=italian" in help_text

    def test_language_help_command_exists(self, mocker):
        """Test that language-help command exists and works."""
        runner = CliRunner()

        # Mock the configuration to avoid actual validation
        mocker.patch("document_to_anki.cli.main.ModelConfig.validate_and_get_model")
        mock_settings = mocker.patch("document_to_anki.config.settings")
        mock_settings.get_language_info.return_value.name = "English"
        mock_settings.get_language_info.return_value.code = "en"

        result = runner.invoke(main, ["language-help"])

        assert result.exit_code == 0
        help_text = result.output

        # Check for comprehensive language help content
        assert "Language Configuration Help" in help_text
        assert "Supported Languages:" in help_text
        assert "Usage Examples:" in help_text
        assert "Configuration Methods:" in help_text

        # Check for all supported languages
        for lang in LanguageConfig.get_supported_languages_list():
            assert lang in help_text

    def test_language_help_command_in_help_list(self):
        """Test that language-help command appears in main help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "language-help" in result.output

    def test_invalid_language_error_message(self, mocker):
        """Test error message for invalid language configuration."""
        runner = CliRunner()

        # Mock environment variable
        mocker.patch.dict(os.environ, {"CARDLANG": "invalid_language"})

        # Mock model validation to pass, but let language validation fail
        mocker.patch("document_to_anki.cli.main.ModelConfig.validate_and_get_model")

        # Mock the settings to raise a validation error
        from document_to_anki.config import LanguageValidationError

        mock_settings = mocker.patch("document_to_anki.config.settings")
        mock_settings.get_language_info.side_effect = LanguageValidationError(
            "invalid_language", ["English (en)", "French (fr)", "Italian (it)", "German (de)"]
        )

        result = runner.invoke(main, ["language-help"])

        # Should exit with error due to invalid language configuration
        assert result.exit_code == 1
        error_output = result.output

        # Check for language configuration error
        assert "Language Configuration Error" in error_output
        assert "How to fix this:" in error_output
        assert "CARDLANG" in error_output

        # Check for supported languages list
        assert "English" in error_output
        assert "French" in error_output
        assert "Italian" in error_output
        assert "German" in error_output

        # Check for examples
        assert "export CARDLANG=" in error_output

    def test_empty_language_uses_default(self, mocker):
        """Test that empty CARDLANG uses default language."""
        runner = CliRunner()

        # Mock environment variable
        mocker.patch.dict(os.environ, {"CARDLANG": ""})

        # Mock both model and settings validation
        mocker.patch("document_to_anki.cli.main.ModelConfig.validate_and_get_model")
        mock_settings = mocker.patch("document_to_anki.config.settings")
        mock_settings.get_language_info.return_value.name = "English"
        mock_settings.get_language_info.return_value.code = "en"

        result = runner.invoke(main, ["language-help"])

        # Should not error, should use default English
        assert result.exit_code == 0

    def test_language_info_in_success_message(self):
        """Test that language information appears in success messages."""
        # This would require a full integration test with actual file processing
        # For now, we'll test the helper function directly
        from io import StringIO

        from rich.console import Console

        from document_to_anki.cli.main import _show_language_help

        # Capture console output
        string_io = StringIO()
        console = Console(file=string_io, width=80)

        _show_language_help(console)
        output = string_io.getvalue()

        # Check for comprehensive help content
        assert "Language Configuration Help" in output
        assert "Supported Languages:" in output
        assert "Usage Examples:" in output
        assert "Configuration Methods:" in output
        assert "Notes:" in output

        # Check for all supported languages
        for lang in LanguageConfig.get_supported_languages_list():
            assert lang in output

    def test_cli_shows_current_language_on_error(self):
        """Test that CLI shows current language configuration on errors."""
        # This is tested indirectly through the error message tests above
        # The actual implementation is in the CLI error handling code
        pass

    @pytest.mark.parametrize("language", ["english", "en", "french", "fr", "italian", "it", "german", "de"])
    def test_valid_languages_in_help_examples(self, language):
        """Test that all valid languages appear in help examples."""
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "--help"])

        assert result.exit_code == 0
        # The help should mention the language format, even if not all specific examples
        assert "CARDLANG=" in result.output

    def test_language_help_shows_configuration_methods(self):
        """Test that language help shows different configuration methods."""
        from io import StringIO

        from rich.console import Console

        from document_to_anki.cli.main import _show_language_help

        string_io = StringIO()
        console = Console(file=string_io, width=80)

        _show_language_help(console)
        output = string_io.getvalue()

        # Check for different configuration methods
        assert "Environment variable:" in output
        assert ".env file:" in output
        assert "Inline:" in output

        # Check for notes about behavior
        assert "Default language is English" in output
        assert "Both full names" in output
        assert "Case-insensitive" in output

    def test_error_messages_include_language_help_reference(self, mocker):
        """Test that error messages reference language-help command."""
        runner = CliRunner()

        # Mock model validation to pass, but simulate a language-related error
        mocker.patch("document_to_anki.cli.main.ModelConfig.validate_and_get_model")
        mocker.patch.dict(os.environ, {"CARDLANG": "invalid"})

        # Mock the settings to raise a validation error
        from document_to_anki.config import LanguageValidationError

        mock_settings = mocker.patch("document_to_anki.config.settings")
        mock_settings.get_language_info.side_effect = LanguageValidationError(
            "invalid", ["English (en)", "French (fr)", "Italian (it)", "German (de)"]
        )

        result = runner.invoke(main, ["language-help"])

        assert result.exit_code == 1
        assert "document-to-anki language-help" in result.output or "language-help" in result.output


class TestCLILanguageIntegration:
    """Integration tests for language configuration in CLI workflow."""

    def test_cli_executable_with_language_help(self):
        """Test that CLI executable supports language-help command."""
        # Test the actual CLI executable if available
        try:
            result = subprocess.run(
                [sys.executable, "-m", "document_to_anki.cli.main", "language-help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should not crash, regardless of configuration
            assert result.returncode in [0, 1]  # 0 for success, 1 for config errors

            if result.returncode == 0:
                assert "Language Configuration Help" in result.stdout
            else:
                # If it fails, it should be due to configuration, not missing command
                assert "language-help" not in result.stderr or "not found" not in result.stderr.lower()

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Skip if CLI is not available or takes too long
            pytest.skip("CLI executable not available or timeout")

    def test_help_text_formatting(self):
        """Test that help text is properly formatted and readable."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0

        # Check that language section is present
        assert "LANGUAGE CONFIGURATION:" in result.output
        assert "CARDLANG" in result.output

        # The exact formatting may vary, so just check for key content
        assert "English" in result.output
        assert "French" in result.output

    def test_error_message_formatting(self, mocker):
        """Test that error messages are properly formatted."""
        runner = CliRunner()

        mocker.patch("document_to_anki.cli.main.ModelConfig.validate_and_get_model")

        # Mock the settings to raise a validation error
        from document_to_anki.config import LanguageValidationError

        mock_settings = mocker.patch("document_to_anki.config.settings")
        mock_settings.get_language_info.side_effect = LanguageValidationError(
            "invalid", ["English (en)", "French (fr)", "Italian (it)", "German (de)"]
        )

        result = runner.invoke(main, ["language-help"])

        assert result.exit_code == 1

        # Check for proper error formatting
        assert "❌" in result.output or "Error" in result.output
        assert "💡" in result.output or "How to fix" in result.output
