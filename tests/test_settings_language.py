"""Tests for Settings class language configuration."""

import os

# pytest-mock provides the mocker fixture
import pytest

from document_to_anki.config import LanguageInfo, Settings


class TestSettingsLanguage:
    """Test cases for Settings class language configuration."""

    def test_cardlang_field_default(self, mocker):
        """Test that cardlang field defaults to English."""
        mocker.patch.dict(os.environ, {}, clear=True)
        # Create Settings without loading from .env file
        settings = Settings(_env_file=None)
        assert settings.cardlang == "english"

    def test_cardlang_field_from_env_var(self, mocker):
        """Test cardlang field loading from CARDLANG environment variable."""
        mocker.patch.dict(os.environ, {"CARDLANG": "french"})
        settings = Settings()
        assert settings.cardlang == "french"

    def test_cardlang_field_normalization(self, mocker):
        """Test that cardlang field normalizes input values."""
        test_cases = [
            ("ENGLISH", "english"),
            ("French", "french"),
            ("ITALIAN", "italian"),
            ("german", "german"),
            ("EN", "en"),
            ("Fr", "fr"),
            ("IT", "it"),
            ("de", "de"),
            ("  english  ", "english"),
            ("\tFR\n", "fr"),
        ]

        for input_value, expected_normalized in test_cases:
            mocker.patch.dict(os.environ, {"CARDLANG": input_value})
            settings = Settings()
            assert settings.cardlang == expected_normalized

    def test_cardlang_field_validation_valid_languages(self, mocker):
        """Test cardlang field validation with valid languages."""
        valid_languages = ["english", "en", "french", "fr", "italian", "it", "german", "de"]

        for lang in valid_languages:
            mocker.patch.dict(os.environ, {"CARDLANG": lang})
            # Should not raise any exceptions
            settings = Settings()
            assert settings.cardlang in ["english", "en", "french", "fr", "italian", "it", "german", "de"]

    def test_cardlang_field_validation_invalid_languages(self, mocker):
        """Test cardlang field validation with invalid languages."""
        invalid_languages = ["spanish", "zh", "invalid", "123", "portuguese"]

        for lang in invalid_languages:
            mocker.patch.dict(os.environ, {"CARDLANG": lang})
            with pytest.raises(ValueError) as exc_info:
                Settings()

            error_msg = str(exc_info.value)
            assert f"Unsupported language '{lang}'" in error_msg
            assert "Supported languages:" in error_msg

    def test_cardlang_field_empty_value_fallback(self, mocker):
        """Test cardlang field fallback to English when empty."""
        empty_values = ["", "   ", "\t\n"]

        for empty_value in empty_values:
            mocker.patch.dict(os.environ, {"CARDLANG": empty_value})
            settings = Settings()
            assert settings.cardlang == "english"

    def test_cardlang_field_missing_env_var(self, mocker):
        """Test cardlang field when CARDLANG environment variable is not set."""
        mocker.patch.dict(os.environ, {}, clear=True)
        pass
        settings = Settings(_env_file=None)
        assert settings.cardlang == "english"

    def test_get_language_info_method(self, mocker):
        """Test get_language_info helper method."""
        # Test with English (default)
        mocker.patch.dict(os.environ, {}, clear=True)
        pass
        settings = Settings(_env_file=None)
        info = settings.get_language_info()

        assert isinstance(info, LanguageInfo)
        assert info.code == "en"
        assert info.name == "English"
        assert info.prompt_key == "english"

        # Test with French
        mocker.patch.dict(os.environ, {"CARDLANG": "french"})
        pass
        settings = Settings()
        info = settings.get_language_info()

        assert info.code == "fr"
        assert info.name == "French"
        assert info.prompt_key == "french"

        # Test with Italian ISO code
        mocker.patch.dict(os.environ, {"CARDLANG": "it"})
        pass
        settings = Settings()
        info = settings.get_language_info()

        assert info.code == "it"
        assert info.name == "Italian"
        assert info.prompt_key == "italian"

    def test_get_language_name_method(self, mocker):
        """Test get_language_name helper method."""
        # Test with default English
        mocker.patch.dict(os.environ, {}, clear=True)
        pass
        settings = Settings(_env_file=None)
        assert settings.get_language_name() == "English"

        # Test with different languages
        test_cases = [
            ("french", "French"),
            ("fr", "French"),
            ("italian", "Italian"),
            ("it", "Italian"),
            ("german", "German"),
            ("de", "German"),
            ("english", "English"),
            ("en", "English"),
        ]

        for cardlang_value, expected_name in test_cases:
            mocker.patch.dict(os.environ, {"CARDLANG": cardlang_value})
            pass
            settings = Settings()
            assert settings.get_language_name() == expected_name

    def test_get_language_code_method(self, mocker):
        """Test get_language_code helper method."""
        # Test with default English
        mocker.patch.dict(os.environ, {}, clear=True)
        pass
        settings = Settings(_env_file=None)
        assert settings.get_language_code() == "en"

        # Test with different languages
        test_cases = [
            ("french", "fr"),
            ("fr", "fr"),
            ("italian", "it"),
            ("it", "it"),
            ("german", "de"),
            ("de", "de"),
            ("english", "en"),
            ("en", "en"),
        ]

        for cardlang_value, expected_code in test_cases:
            mocker.patch.dict(os.environ, {"CARDLANG": cardlang_value})
            pass
            settings = Settings()
            assert settings.get_language_code() == expected_code

    def test_get_prompt_key_method(self, mocker):
        """Test get_prompt_key helper method."""
        # Test with default English
        mocker.patch.dict(os.environ, {}, clear=True)
        pass
        settings = Settings(_env_file=None)
        assert settings.get_prompt_key() == "english"

        # Test with different languages
        test_cases = [
            ("french", "french"),
            ("fr", "french"),
            ("italian", "italian"),
            ("it", "italian"),
            ("german", "german"),
            ("de", "german"),
            ("english", "english"),
            ("en", "english"),
        ]

        for cardlang_value, expected_prompt_key in test_cases:
            mocker.patch.dict(os.environ, {"CARDLANG": cardlang_value})
            pass
            settings = Settings()
            assert settings.get_prompt_key() == expected_prompt_key

    def test_language_configuration_integration_with_other_settings(self, mocker):
        """Test that language configuration works alongside other settings."""
        env_vars = {
            "CARDLANG": "german",
            "MODEL": "gemini/gemini-2.5-pro",
            "LOG_LEVEL": "DEBUG",
            "MAX_FILE_SIZE_MB": "100",
        }

        mocker.patch.dict(os.environ, env_vars)
        pass
        settings = Settings()

        # Test language configuration
        assert settings.cardlang == "german"
        assert settings.get_language_code() == "de"
        assert settings.get_language_name() == "German"

        # Test other settings are not affected
        assert settings.model == "gemini/gemini-2.5-pro"
        assert settings.log_level == "DEBUG"
        assert settings.max_file_size_mb == 100

    def test_settings_language_methods_consistency(self, mocker):
        """Test that all language helper methods are consistent."""
        test_languages = ["english", "french", "italian", "german", "en", "fr", "it", "de"]

        for lang in test_languages:
            mocker.patch.dict(os.environ, {"CARDLANG": lang})
            pass
            settings = Settings()

            # Get information through different methods
            info = settings.get_language_info()
            name = settings.get_language_name()
            code = settings.get_language_code()
            prompt_key = settings.get_prompt_key()

            # Verify consistency
            assert info.name == name
            assert info.code == code
            assert info.prompt_key == prompt_key

    def test_cardlang_field_case_insensitive(self, mocker):
        """Test that cardlang field is case insensitive."""
        case_variations = [
            "ENGLISH",
            "English",
            "english",
            "eNgLiSh",
            "FRENCH",
            "French",
            "french",
            "fReNcH",
            "EN",
            "En",
            "en",
            "eN",
            "FR",
            "Fr",
            "fr",
            "fR",
        ]

        for lang_variation in case_variations:
            mocker.patch.dict(os.environ, {"CARDLANG": lang_variation})
            pass
            # Should not raise any exceptions
            settings = Settings()
            assert settings.cardlang.lower() in ["english", "french", "en", "fr"]

    def test_cardlang_field_whitespace_handling(self, mocker):
        """Test that cardlang field handles whitespace properly."""
        whitespace_cases = [
            "  english  ",
            "\tenglish\n",
            " french ",
            "\tit\t",
            "  de  ",
        ]

        for lang_with_whitespace in whitespace_cases:
            mocker.patch.dict(os.environ, {"CARDLANG": lang_with_whitespace})
            pass
            settings = Settings()
            # Should normalize to clean value
            assert settings.cardlang == lang_with_whitespace.strip().lower()

    def test_backward_compatibility_default_behavior(self, mocker):
        """Test backward compatibility - defaults to English when not configured."""
        # Simulate existing user with no CARDLANG set
        mocker.patch.dict(os.environ, {}, clear=True)
        pass
        settings = Settings(_env_file=None)

        # Should default to English (not French as was hardcoded before)
        assert settings.cardlang == "english"
        assert settings.get_language_code() == "en"
        assert settings.get_language_name() == "English"
        assert settings.get_prompt_key() == "english"

    def test_migration_guidance_in_error_messages(self, mocker):
        """Test that error messages provide helpful migration guidance."""
        mocker.patch.dict(os.environ, {"CARDLANG": "spanish"})
        pass
        with pytest.raises(ValueError) as exc_info:
            Settings()

        error_msg = str(exc_info.value)
        # Should mention supported languages for migration guidance
        assert "Supported languages:" in error_msg
        assert "English" in error_msg
        assert "French" in error_msg
        assert "Italian" in error_msg
        assert "German" in error_msg

    def test_settings_instantiation_with_language_config(self, mocker):
        """Test Settings instantiation with various language configurations."""
        # Test that Settings can be instantiated multiple times with different configs
        configs = [
            ("english", "en", "English"),
            ("fr", "fr", "French"),
            ("ITALIAN", "it", "Italian"),
            ("de", "de", "German"),
        ]

        for cardlang, expected_code, expected_name in configs:
            mocker.patch.dict(os.environ, {"CARDLANG": cardlang})
            pass
            settings = Settings()

            assert settings.get_language_code() == expected_code
            assert settings.get_language_name() == expected_name

            # Test that settings object is properly configured
            assert hasattr(settings, "cardlang")
            assert hasattr(settings, "get_language_info")
            assert hasattr(settings, "get_language_name")
            assert hasattr(settings, "get_language_code")
            assert hasattr(settings, "get_prompt_key")
