"""Tests for LanguageConfig utility class."""

import pytest

from document_to_anki.config import LanguageConfig, LanguageInfo, LanguageValidationError


class TestLanguageConfig:
    """Test cases for LanguageConfig class."""

    def test_supported_languages_structure(self):
        """Test that SUPPORTED_LANGUAGES has correct structure."""
        assert isinstance(LanguageConfig.SUPPORTED_LANGUAGES, dict)

        # Check that all entries have required keys
        for _, lang_data in LanguageConfig.SUPPORTED_LANGUAGES.items():
            assert isinstance(lang_data, dict)
            assert "code" in lang_data
            assert "name" in lang_data
            assert "prompt_key" in lang_data
            assert isinstance(lang_data["code"], str)
            assert isinstance(lang_data["name"], str)
            assert isinstance(lang_data["prompt_key"], str)

    def test_default_language(self):
        """Test that default language is properly defined."""
        assert LanguageConfig.DEFAULT_LANGUAGE == "english"
        assert LanguageConfig.DEFAULT_LANGUAGE in LanguageConfig.SUPPORTED_LANGUAGES

    def test_normalize_language_valid_inputs(self):
        """Test language normalization with valid inputs."""
        # Test full language names
        assert LanguageConfig.normalize_language("English") == "english"
        assert LanguageConfig.normalize_language("FRENCH") == "french"
        assert LanguageConfig.normalize_language("italian") == "italian"
        assert LanguageConfig.normalize_language("German") == "german"

        # Test ISO codes
        assert LanguageConfig.normalize_language("EN") == "en"
        assert LanguageConfig.normalize_language("fr") == "fr"
        assert LanguageConfig.normalize_language("IT") == "it"
        assert LanguageConfig.normalize_language("de") == "de"

        # Test with whitespace
        assert LanguageConfig.normalize_language("  english  ") == "english"
        assert LanguageConfig.normalize_language("\tFR\n") == "fr"

    def test_normalize_language_empty_input(self):
        """Test language normalization with empty input."""
        assert LanguageConfig.normalize_language("") == "english"
        assert LanguageConfig.normalize_language(None) == "english"

    def test_normalize_language_invalid_inputs(self):
        """Test language normalization with invalid inputs."""
        with pytest.raises(LanguageValidationError) as exc_info:
            LanguageConfig.normalize_language("spanish")

        assert "spanish" in str(exc_info.value)
        assert "Supported languages:" in str(exc_info.value)

        with pytest.raises(LanguageValidationError):
            LanguageConfig.normalize_language("zh")

        with pytest.raises(LanguageValidationError):
            LanguageConfig.normalize_language("invalid")

    def test_validate_language_valid_inputs(self):
        """Test language validation with valid inputs."""
        # Test all supported language keys
        for lang_key in LanguageConfig.SUPPORTED_LANGUAGES.keys():
            assert LanguageConfig.validate_language(lang_key) is True

        # Test case insensitive
        assert LanguageConfig.validate_language("ENGLISH") is True
        assert LanguageConfig.validate_language("Fr") is True

        # Test with whitespace
        assert LanguageConfig.validate_language("  italian  ") is True

    def test_validate_language_empty_input(self):
        """Test language validation with empty input."""
        assert LanguageConfig.validate_language("") is True
        assert LanguageConfig.validate_language(None) is True

    def test_validate_language_invalid_inputs(self):
        """Test language validation with invalid inputs."""
        assert LanguageConfig.validate_language("spanish") is False
        assert LanguageConfig.validate_language("zh") is False
        assert LanguageConfig.validate_language("invalid") is False
        assert LanguageConfig.validate_language("123") is False

    def test_get_language_name(self):
        """Test getting language display names."""
        assert LanguageConfig.get_language_name("english") == "English"
        assert LanguageConfig.get_language_name("en") == "English"
        assert LanguageConfig.get_language_name("FRENCH") == "French"
        assert LanguageConfig.get_language_name("fr") == "French"
        assert LanguageConfig.get_language_name("italian") == "Italian"
        assert LanguageConfig.get_language_name("it") == "Italian"
        assert LanguageConfig.get_language_name("german") == "German"
        assert LanguageConfig.get_language_name("de") == "German"

    def test_get_language_name_invalid(self):
        """Test getting language name with invalid input."""
        with pytest.raises(LanguageValidationError):
            LanguageConfig.get_language_name("spanish")

    def test_get_language_code(self):
        """Test getting ISO language codes."""
        assert LanguageConfig.get_language_code("english") == "en"
        assert LanguageConfig.get_language_code("en") == "en"
        assert LanguageConfig.get_language_code("FRENCH") == "fr"
        assert LanguageConfig.get_language_code("fr") == "fr"
        assert LanguageConfig.get_language_code("italian") == "it"
        assert LanguageConfig.get_language_code("it") == "it"
        assert LanguageConfig.get_language_code("german") == "de"
        assert LanguageConfig.get_language_code("de") == "de"

    def test_get_language_code_invalid(self):
        """Test getting language code with invalid input."""
        with pytest.raises(LanguageValidationError):
            LanguageConfig.get_language_code("spanish")

    def test_get_prompt_key(self):
        """Test getting prompt template keys."""
        assert LanguageConfig.get_prompt_key("english") == "english"
        assert LanguageConfig.get_prompt_key("en") == "english"
        assert LanguageConfig.get_prompt_key("FRENCH") == "french"
        assert LanguageConfig.get_prompt_key("fr") == "french"
        assert LanguageConfig.get_prompt_key("italian") == "italian"
        assert LanguageConfig.get_prompt_key("it") == "italian"
        assert LanguageConfig.get_prompt_key("german") == "german"
        assert LanguageConfig.get_prompt_key("de") == "german"

    def test_get_prompt_key_invalid(self):
        """Test getting prompt key with invalid input."""
        with pytest.raises(LanguageValidationError):
            LanguageConfig.get_prompt_key("spanish")

    def test_get_language_info(self):
        """Test getting structured language information."""
        # Test English
        info = LanguageConfig.get_language_info("english")
        assert isinstance(info, LanguageInfo)
        assert info.code == "en"
        assert info.name == "English"
        assert info.prompt_key == "english"

        # Test French with ISO code
        info = LanguageConfig.get_language_info("fr")
        assert info.code == "fr"
        assert info.name == "French"
        assert info.prompt_key == "french"

        # Test Italian
        info = LanguageConfig.get_language_info("ITALIAN")
        assert info.code == "it"
        assert info.name == "Italian"
        assert info.prompt_key == "italian"

        # Test German
        info = LanguageConfig.get_language_info("de")
        assert info.code == "de"
        assert info.name == "German"
        assert info.prompt_key == "german"

    def test_get_language_info_invalid(self):
        """Test getting language info with invalid input."""
        with pytest.raises(LanguageValidationError):
            LanguageConfig.get_language_info("spanish")

    def test_get_supported_languages_list(self):
        """Test getting list of supported languages."""
        languages = LanguageConfig.get_supported_languages_list()

        assert isinstance(languages, list)
        assert len(languages) == 4  # English, French, Italian, German

        # Check that all expected languages are present
        language_names = [lang.split(" (")[0] for lang in languages]
        assert "English" in language_names
        assert "French" in language_names
        assert "Italian" in language_names
        assert "German" in language_names

        # Check format: "Name (code)"
        for lang in languages:
            assert " (" in lang
            assert lang.endswith(")")

        # Check that list is sorted
        assert languages == sorted(languages)

    def test_get_all_language_keys(self):
        """Test getting all language keys including aliases."""
        keys = LanguageConfig.get_all_language_keys()

        assert isinstance(keys, list)
        assert len(keys) == 8  # 4 languages × 2 keys each (name + code)

        # Check that all expected keys are present
        expected_keys = ["english", "en", "french", "fr", "italian", "it", "german", "de"]
        for key in expected_keys:
            assert key in keys

    def test_language_validation_error_structure(self):
        """Test LanguageValidationError exception structure."""
        supported = ["english", "french"]
        error = LanguageValidationError("spanish", supported)

        assert error.language == "spanish"
        assert error.supported_languages == supported
        assert "spanish" in str(error)
        assert "english, french" in str(error)

    def test_case_insensitive_operations(self):
        """Test that all operations are case insensitive."""
        test_cases = [
            ("ENGLISH", "english"),
            ("French", "french"),
            ("ITALIAN", "italian"),
            ("german", "german"),
            ("EN", "en"),
            ("Fr", "fr"),
            ("IT", "it"),
            ("de", "de"),
        ]

        for input_lang, expected_normalized in test_cases:
            # Test normalization
            assert LanguageConfig.normalize_language(input_lang) == expected_normalized

            # Test validation
            assert LanguageConfig.validate_language(input_lang) is True

            # Test info retrieval
            info = LanguageConfig.get_language_info(input_lang)
            assert isinstance(info, LanguageInfo)

    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        test_cases = [
            "  english  ",
            "\tenglish\n",
            " french ",
            "\tit\t",
            "  de  ",
        ]

        for lang_with_whitespace in test_cases:
            # Should not raise exceptions
            assert LanguageConfig.validate_language(lang_with_whitespace) is True
            normalized = LanguageConfig.normalize_language(lang_with_whitespace)
            assert normalized == lang_with_whitespace.strip().lower()

    def test_language_info_dataclass(self):
        """Test LanguageInfo dataclass functionality."""
        info = LanguageInfo(code="en", name="English", prompt_key="english")

        assert info.code == "en"
        assert info.name == "English"
        assert info.prompt_key == "english"

        # Test string representation
        assert "en" in str(info)
        assert "English" in str(info)
        assert "english" in str(info)

    def test_comprehensive_language_coverage(self):
        """Test that all required languages are supported."""
        required_languages = {"english": "en", "french": "fr", "italian": "it", "german": "de"}

        for lang_name, lang_code in required_languages.items():
            # Test both name and code are supported
            assert LanguageConfig.validate_language(lang_name) is True
            assert LanguageConfig.validate_language(lang_code) is True

            # Test they normalize to the same values
            assert LanguageConfig.get_language_code(lang_name) == lang_code
            assert LanguageConfig.get_language_code(lang_code) == lang_code

            # Test info consistency
            info_from_name = LanguageConfig.get_language_info(lang_name)
            info_from_code = LanguageConfig.get_language_info(lang_code)
            assert info_from_name.code == info_from_code.code
            assert info_from_name.name == info_from_code.name
