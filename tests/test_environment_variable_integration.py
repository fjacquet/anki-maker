"""
Integration tests for environment variable parsing and language configuration defaults.

This module tests the complete integration of language configuration with environment
variables, including parsing, validation, and default behavior.
"""

import os
import tempfile
from pathlib import Path

import pytest

from document_to_anki.config import Settings


class TestEnvironmentVariableIntegration:
    """Integration tests for environment variable parsing and defaults."""

    def test_cardlang_environment_variable_parsing(self, mocker):
        """Test CARDLANG environment variable parsing for all supported languages."""
        test_cases = [
            ("english", "english"),
            ("ENGLISH", "english"),
            ("English", "english"),
            ("french", "french"),
            ("FRENCH", "french"),
            ("French", "french"),
            ("italian", "italian"),
            ("ITALIAN", "italian"),
            ("Italian", "italian"),
            ("german", "german"),
            ("GERMAN", "german"),
            ("German", "german"),
            ("en", "en"),
            ("EN", "en"),
            ("En", "en"),
            ("fr", "fr"),
            ("FR", "fr"),
            ("Fr", "fr"),
            ("it", "it"),
            ("IT", "it"),
            ("It", "it"),
            ("de", "de"),
            ("DE", "de"),
            ("De", "de"),
        ]

        for env_value, expected_normalized in test_cases:
            mocker.patch.dict(os.environ, {"CARDLANG": env_value}, clear=True)
            settings = Settings(_env_file=None)
            assert settings.cardlang == expected_normalized

    def test_cardlang_environment_variable_with_whitespace(self, mocker):
        """Test CARDLANG environment variable parsing with whitespace."""
        whitespace_cases = [
            ("  english  ", "english"),
            ("\tenglish\n", "english"),
            (" \t english \n ", "english"),
            ("  french  ", "french"),
            ("\tfrench\n", "french"),
            (" \t french \n ", "french"),
            ("  italian  ", "italian"),
            ("\titalian\n", "italian"),
            (" \t italian \n ", "italian"),
            ("  german  ", "german"),
            ("\tgerman\n", "german"),
            (" \t german \n ", "german"),
            ("  en  ", "en"),
            ("\ten\n", "en"),
            (" \t en \n ", "en"),
            ("  fr  ", "fr"),
            ("\tfr\n", "fr"),
            (" \t fr \n ", "fr"),
            ("  it  ", "it"),
            ("\tit\n", "it"),
            (" \t it \n ", "it"),
            ("  de  ", "de"),
            ("\tde\n", "de"),
            (" \t de \n ", "de"),
        ]

        for env_value, expected_normalized in whitespace_cases:
            mocker.patch.dict(os.environ, {"CARDLANG": env_value}, clear=True)
            settings = Settings(_env_file=None)
            assert settings.cardlang == expected_normalized

    def test_cardlang_environment_variable_invalid_values(self, mocker):
        """Test CARDLANG environment variable with invalid values."""
        invalid_values = [
            "spanish",
            "portuguese",
            "chinese",
            "japanese",
            "invalid",
            "xyz",
            "123",
            "es",
            "pt",
            "zh",
            "ja",
            "notlang",
        ]

        for invalid_value in invalid_values:
            mocker.patch.dict(os.environ, {"CARDLANG": invalid_value}, clear=True)
            with pytest.raises(ValueError) as exc_info:
                Settings(_env_file=None)

            error_msg = str(exc_info.value)
            assert f"Unsupported language '{invalid_value}'" in error_msg
            assert "Supported languages:" in error_msg

    def test_cardlang_environment_variable_empty_values(self, mocker):
        """Test CARDLANG environment variable with empty values."""
        empty_values = ["", "   ", "\t", "\n", "\t\n", "  \t  \n  "]

        for empty_value in empty_values:
            mocker.patch.dict(os.environ, {"CARDLANG": empty_value}, clear=True)
            settings = Settings(_env_file=None)
            # Empty values should default to English
            assert settings.cardlang == "english"

    def test_cardlang_environment_variable_not_set(self, mocker):
        """Test behavior when CARDLANG environment variable is not set."""
        # Clear all environment variables
        mocker.patch.dict(os.environ, {}, clear=True)
        settings = Settings(_env_file=None)

        # Should default to English
        assert settings.cardlang == "english"
        assert settings.get_language_name() == "English"
        assert settings.get_language_code() == "en"
        assert settings.get_prompt_key() == "english"

    def test_cardlang_with_env_file_loading(self, mocker):
        """Test CARDLANG loading from .env file."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as env_file:
            env_file.write("CARDLANG=german\n")
            env_file.write("MODEL=gemini/gemini-2.5-pro\n")
            env_file.write("LOG_LEVEL=DEBUG\n")
            env_file_path = env_file.name

        try:
            # Clear environment variables
            mocker.patch.dict(os.environ, {}, clear=True)

            # Load settings from .env file
            settings = Settings(_env_file=env_file_path)

            assert settings.cardlang == "german"
            assert settings.get_language_name() == "German"
            assert settings.get_language_code() == "de"

            # Other settings should also be loaded
            assert settings.model == "gemini/gemini-2.5-pro"
            assert settings.log_level == "DEBUG"

        finally:
            # Clean up
            Path(env_file_path).unlink(missing_ok=True)

    def test_environment_variable_overrides_env_file(self, mocker):
        """Test that environment variables override .env file values."""
        # Create temporary .env file with one language
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as env_file:
            env_file.write("CARDLANG=french\n")
            env_file.write("MODEL=gemini/gemini-2.5-flash\n")
            env_file_path = env_file.name

        try:
            # Set environment variable to different language
            mocker.patch.dict(os.environ, {"CARDLANG": "italian"}, clear=True)

            # Load settings - env var should override .env file
            settings = Settings(_env_file=env_file_path)

            assert settings.cardlang == "italian"  # From environment variable
            assert settings.model == "gemini/gemini-2.5-flash"  # From .env file

        finally:
            # Clean up
            Path(env_file_path).unlink(missing_ok=True)

    def test_cardlang_with_other_environment_variables(self, mocker):
        """Test CARDLANG integration with other environment variables."""
        env_vars = {
            "CARDLANG": "german",
            "MODEL": "gemini/gemini-2.5-pro",
            "LOG_LEVEL": "DEBUG",
            "MAX_FILE_SIZE_MB": "150",
            "GEMINI_API_KEY": "test-api-key",
        }

        mocker.patch.dict(os.environ, env_vars, clear=True)
        settings = Settings(_env_file=None)

        # Language configuration
        assert settings.cardlang == "german"
        assert settings.get_language_name() == "German"
        assert settings.get_language_code() == "de"
        assert settings.get_prompt_key() == "german"

        # Other settings should not be affected
        assert settings.model == "gemini/gemini-2.5-pro"
        assert settings.log_level == "DEBUG"
        assert settings.max_file_size_mb == 150
        assert settings.gemini_api_key == "test-api-key"

    def test_cardlang_case_insensitive_environment_parsing(self, mocker):
        """Test that CARDLANG environment variable parsing is case insensitive."""
        case_variations = [
            ("ENGLISH", "english"),
            ("English", "english"),
            ("eNgLiSh", "english"),
            ("FRENCH", "french"),
            ("French", "french"),
            ("fReNcH", "french"),
            ("ITALIAN", "italian"),
            ("Italian", "italian"),
            ("iTaLiAn", "italian"),
            ("GERMAN", "german"),
            ("German", "german"),
            ("gErMaN", "german"),
            ("EN", "en"),
            ("En", "en"),
            ("eN", "en"),
            ("FR", "fr"),
            ("Fr", "fr"),
            ("fR", "fr"),
            ("IT", "it"),
            ("It", "it"),
            ("iT", "it"),
            ("DE", "de"),
            ("De", "de"),
            ("dE", "de"),
        ]

        for env_value, expected_normalized in case_variations:
            mocker.patch.dict(os.environ, {"CARDLANG": env_value}, clear=True)
            settings = Settings(_env_file=None)
            assert settings.cardlang == expected_normalized

    def test_settings_instantiation_multiple_times(self, mocker):
        """Test that Settings can be instantiated multiple times with different CARDLANG values."""
        languages = ["english", "french", "italian", "german", "en", "fr", "it", "de"]

        for language in languages:
            mocker.patch.dict(os.environ, {"CARDLANG": language}, clear=True)
            settings = Settings(_env_file=None)

            # Verify language configuration
            assert settings.cardlang in ["english", "french", "italian", "german", "en", "fr", "it", "de"]

            # Verify helper methods work
            lang_info = settings.get_language_info()
            assert lang_info.name in ["English", "French", "Italian", "German"]
            assert lang_info.code in ["en", "fr", "it", "de"]
            assert lang_info.prompt_key in ["english", "french", "italian", "german"]

    def test_backward_compatibility_default_behavior(self, mocker):
        """Test backward compatibility - defaults to English when not configured."""
        # Simulate existing user with no CARDLANG set (pre-language-config version)
        mocker.patch.dict(
            os.environ,
            {
                "MODEL": "gemini/gemini-2.5-flash",
                "LOG_LEVEL": "INFO",
                # No CARDLANG set
            },
            clear=True,
        )

        settings = Settings(_env_file=None)

        # Should default to English (not French as was hardcoded before)
        assert settings.cardlang == "english"
        assert settings.get_language_code() == "en"
        assert settings.get_language_name() == "English"
        assert settings.get_prompt_key() == "english"

        # Other settings should work normally
        assert settings.model == "gemini/gemini-2.5-flash"
        assert settings.log_level == "INFO"

    def test_migration_from_hardcoded_french(self, mocker):
        """Test migration scenario from hardcoded French to configurable system."""
        # Test that users can explicitly set French if they want to maintain previous behavior
        mocker.patch.dict(os.environ, {"CARDLANG": "french"}, clear=True)
        settings = Settings(_env_file=None)

        assert settings.cardlang == "french"
        assert settings.get_language_code() == "fr"
        assert settings.get_language_name() == "French"
        assert settings.get_prompt_key() == "french"

    def test_error_messages_provide_migration_guidance(self, mocker):
        """Test that error messages provide helpful migration guidance."""
        invalid_languages = ["spanish", "portuguese", "chinese"]

        for invalid_lang in invalid_languages:
            mocker.patch.dict(os.environ, {"CARDLANG": invalid_lang}, clear=True)

            with pytest.raises(ValueError) as exc_info:
                Settings(_env_file=None)

            error_msg = str(exc_info.value)

            # Should mention the invalid language
            assert invalid_lang in error_msg

            # Should provide list of supported languages for migration
            assert "Supported languages:" in error_msg
            assert "English" in error_msg
            assert "French" in error_msg
            assert "Italian" in error_msg
            assert "German" in error_msg

    def test_env_file_with_invalid_cardlang(self, mocker):
        """Test .env file with invalid CARDLANG value."""
        # Create temporary .env file with invalid language
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as env_file:
            env_file.write("CARDLANG=spanish\n")
            env_file.write("MODEL=gemini/gemini-2.5-flash\n")
            env_file_path = env_file.name

        try:
            mocker.patch.dict(os.environ, {}, clear=True)

            with pytest.raises(ValueError) as exc_info:
                Settings(_env_file=env_file_path)

            error_msg = str(exc_info.value)
            assert "spanish" in error_msg
            assert "Supported languages:" in error_msg

        finally:
            # Clean up
            Path(env_file_path).unlink(missing_ok=True)

    def test_env_file_with_empty_cardlang(self, mocker):
        """Test .env file with empty CARDLANG value."""
        # Create temporary .env file with empty language
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as env_file:
            env_file.write("CARDLANG=\n")
            env_file.write("MODEL=gemini/gemini-2.5-flash\n")
            env_file_path = env_file.name

        try:
            mocker.patch.dict(os.environ, {}, clear=True)

            settings = Settings(_env_file=env_file_path)

            # Empty value should default to English
            assert settings.cardlang == "english"
            assert settings.model == "gemini/gemini-2.5-flash"

        finally:
            # Clean up
            Path(env_file_path).unlink(missing_ok=True)

    def test_settings_validation_with_complex_environment(self, mocker):
        """Test Settings validation with complex environment setup."""
        # Set up complex environment with multiple variables
        complex_env = {
            "CARDLANG": "  ITALIAN  ",  # With whitespace and case
            "MODEL": "gemini/gemini-2.5-pro",
            "LOG_LEVEL": "DEBUG",
            "MAX_FILE_SIZE_MB": "200",
            "GEMINI_API_KEY": "test-key-123",
            "OPENAI_API_KEY": "openai-key-456",
            # Add some unrelated environment variables
            "PATH": "/usr/bin:/bin",
            "HOME": "/home/user",
            "LANG": "en_US.UTF-8",
        }

        mocker.patch.dict(os.environ, complex_env, clear=True)
        settings = Settings(_env_file=None)

        # Language should be properly normalized
        assert settings.cardlang == "italian"
        assert settings.get_language_name() == "Italian"
        assert settings.get_language_code() == "it"

        # Other settings should be correctly parsed
        assert settings.model == "gemini/gemini-2.5-pro"
        assert settings.log_level == "DEBUG"
        assert settings.max_file_size_mb == 200
        assert settings.gemini_api_key == "test-key-123"

    def test_concurrent_settings_instantiation(self, mocker):
        """Test concurrent Settings instantiation with different CARDLANG values."""
        import concurrent.futures

        results = []
        errors = []

        def create_settings_with_language(language):
            try:
                # Each thread gets its own environment
                thread_env = {"CARDLANG": language}
                mocker.patch.dict(os.environ, thread_env, clear=True)
                settings = Settings(_env_file=None)
                return (language, settings.cardlang, settings.get_language_name())
            except Exception as e:
                errors.append((language, str(e)))
                return None

        languages = ["english", "french", "italian", "german", "en", "fr", "it", "de"]

        # Test with multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(create_settings_with_language, lang) for lang in languages]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Should have no errors
        assert len(errors) == 0

        # All results should be valid
        valid_results = [r for r in results if r is not None]
        assert len(valid_results) == len(languages)

        # Check that each language was processed correctly
        for _original_lang, normalized_lang, language_name in valid_results:
            assert normalized_lang in ["english", "french", "italian", "german", "en", "fr", "it", "de"]
            assert language_name in ["English", "French", "Italian", "German"]

    def test_performance_with_repeated_settings_creation(self, mocker):
        """Test performance with repeated Settings creation."""
        import time

        # Test creating Settings multiple times with same language
        mocker.patch.dict(os.environ, {"CARDLANG": "french"}, clear=True)

        start_time = time.time()
        for _ in range(100):
            settings = Settings(_env_file=None)
            assert settings.cardlang == "french"
        end_time = time.time()

        # Should complete quickly (less than 2 seconds for 100 instantiations)
        assert (end_time - start_time) < 2.0

        # Test creating Settings with different languages
        languages = ["english", "french", "italian", "german"] * 25

        start_time = time.time()
        for language in languages:
            mocker.patch.dict(os.environ, {"CARDLANG": language}, clear=True)
            settings = Settings(_env_file=None)
            assert settings.cardlang == language
        end_time = time.time()

        # Should complete quickly even with different languages
        assert (end_time - start_time) < 2.0
