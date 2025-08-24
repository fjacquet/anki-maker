"""
Comprehensive language configuration validation tests.

This module provides exhaustive testing of all supported language codes,
validation scenarios, and error handling behavior for the language configuration system.
"""

import pytest

from document_to_anki.config import LanguageConfig, LanguageInfo, LanguageValidationError


class TestComprehensiveLanguageValidation:
    """Comprehensive tests for language validation scenarios."""

    def test_all_supported_language_codes_validation(self):
        """Test validation of all supported language codes and formats."""
        # Test all primary language names
        primary_languages = ["english", "french", "italian", "german"]
        for lang in primary_languages:
            assert LanguageConfig.validate_language(lang) is True
            assert LanguageConfig.normalize_language(lang) == lang

        # Test all ISO codes
        iso_codes = ["en", "fr", "it", "de"]
        for code in iso_codes:
            assert LanguageConfig.validate_language(code) is True
            assert LanguageConfig.normalize_language(code) == code

        # Test case variations for all languages
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

        for input_lang, expected_normalized in case_variations:
            assert LanguageConfig.validate_language(input_lang) is True
            assert LanguageConfig.normalize_language(input_lang) == expected_normalized

    def test_whitespace_handling_all_languages(self):
        """Test whitespace handling for all supported languages."""
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

        for input_with_whitespace, expected_normalized in whitespace_cases:
            assert LanguageConfig.validate_language(input_with_whitespace) is True
            assert LanguageConfig.normalize_language(input_with_whitespace) == expected_normalized

    def test_invalid_language_codes_comprehensive(self):
        """Test comprehensive set of invalid language codes."""
        invalid_languages = [
            # Common languages not supported
            "spanish",
            "portuguese",
            "chinese",
            "japanese",
            "korean",
            "russian",
            "arabic",
            "hindi",
            "dutch",
            "swedish",
            "norwegian",
            "danish",
            "finnish",
            "polish",
            "czech",
            "hungarian",
            "greek",
            "turkish",
            "hebrew",
            "thai",
            "vietnamese",
            # Invalid ISO codes
            "es",
            "pt",
            "zh",
            "ja",
            "ko",
            "ru",
            "ar",
            "hi",
            "nl",
            "sv",
            "no",
            "da",
            "fi",
            "pl",
            "cs",
            "hu",
            "el",
            "tr",
            "he",
            "th",
            "vi",
            # Nonsensical inputs
            "invalid",
            "notlang",
            "xyz",
            "123",
            "abc123",
            "lang_test",
            "test-lang",
            "language",
            "code",
            # Empty-like inputs
            "   ",
            "\t\n",
            "null",
            "none",
            "undefined",
            # Special characters
            "en-US",
            "fr-FR",
            "de-DE",
            "it-IT",
            "en_US",
            "fr_FR",
            "de_DE",
            "it_IT",
            "@english",
            "#french",
            "$italian",
            "%german",
            "english!",
            "french?",
            "italian.",
            "german,",
        ]

        for invalid_lang in invalid_languages:
            assert LanguageConfig.validate_language(invalid_lang) is False
            with pytest.raises(LanguageValidationError) as exc_info:
                LanguageConfig.normalize_language(invalid_lang)

            error_msg = str(exc_info.value)
            assert invalid_lang in error_msg
            assert "Supported languages:" in error_msg

    def test_empty_and_none_inputs(self):
        """Test handling of empty and None inputs."""
        truly_empty_inputs = ["", None]

        # Truly empty inputs should be valid and default to English
        for empty_input in truly_empty_inputs:
            assert LanguageConfig.validate_language(empty_input) is True
            assert LanguageConfig.normalize_language(empty_input) == "english"

        # Whitespace-only inputs should be treated as invalid since they strip to empty
        # but are not caught by the initial empty check in validate_language
        whitespace_only_inputs = ["   ", "\t", "\n", "\t\n", "  \t  \n  "]
        for whitespace_input in whitespace_only_inputs:
            # These should be invalid because they strip to empty but don't pass the initial empty check
            assert LanguageConfig.validate_language(whitespace_input) is False
            with pytest.raises(LanguageValidationError):
                LanguageConfig.normalize_language(whitespace_input)

    def test_language_info_retrieval_all_languages(self):
        """Test language info retrieval for all supported languages."""
        expected_language_data = {
            "english": {"code": "en", "name": "English", "prompt_key": "english"},
            "en": {"code": "en", "name": "English", "prompt_key": "english"},
            "french": {"code": "fr", "name": "French", "prompt_key": "french"},
            "fr": {"code": "fr", "name": "French", "prompt_key": "french"},
            "italian": {"code": "it", "name": "Italian", "prompt_key": "italian"},
            "it": {"code": "it", "name": "Italian", "prompt_key": "italian"},
            "german": {"code": "de", "name": "German", "prompt_key": "german"},
            "de": {"code": "de", "name": "German", "prompt_key": "german"},
        }

        for lang_input, expected_data in expected_language_data.items():
            # Test get_language_info
            info = LanguageConfig.get_language_info(lang_input)
            assert isinstance(info, LanguageInfo)
            assert info.code == expected_data["code"]
            assert info.name == expected_data["name"]
            assert info.prompt_key == expected_data["prompt_key"]

            # Test individual getters
            assert LanguageConfig.get_language_code(lang_input) == expected_data["code"]
            assert LanguageConfig.get_language_name(lang_input) == expected_data["name"]
            assert LanguageConfig.get_prompt_key(lang_input) == expected_data["prompt_key"]

    def test_language_validation_error_details(self):
        """Test detailed error information in LanguageValidationError."""
        invalid_languages = ["spanish", "portuguese", "chinese", "xyz", "123"]

        for invalid_lang in invalid_languages:
            with pytest.raises(LanguageValidationError) as exc_info:
                LanguageConfig.normalize_language(invalid_lang)

            error = exc_info.value
            assert error.language == invalid_lang
            assert isinstance(error.supported_languages, list)
            assert len(error.supported_languages) > 0

            # Check that all supported languages are mentioned
            supported_str = str(error.supported_languages)
            assert "English" in supported_str
            assert "French" in supported_str
            assert "Italian" in supported_str
            assert "German" in supported_str

            # Check error message format
            error_msg = str(error)
            assert f"Unsupported language '{invalid_lang}'" in error_msg
            assert "Supported languages:" in error_msg

    def test_supported_languages_list_completeness(self):
        """Test that supported languages list is complete and correctly formatted."""
        languages_list = LanguageConfig.get_supported_languages_list()

        # Should have exactly 4 languages
        assert len(languages_list) == 4

        # Check format: "Name (code)"
        expected_entries = [
            "English (en)",
            "French (fr)",
            "German (de)",
            "Italian (it)",
        ]

        for expected_entry in expected_entries:
            assert expected_entry in languages_list

        # Should be sorted
        assert languages_list == sorted(languages_list)

        # Each entry should follow the pattern
        for entry in languages_list:
            assert " (" in entry
            assert entry.endswith(")")
            assert entry.count("(") == 1
            assert entry.count(")") == 1

    def test_all_language_keys_completeness(self):
        """Test that all language keys are returned correctly."""
        all_keys = LanguageConfig.get_all_language_keys()

        # Should have exactly 8 keys (4 languages × 2 keys each)
        assert len(all_keys) == 8

        expected_keys = ["english", "en", "french", "fr", "italian", "it", "german", "de"]
        for expected_key in expected_keys:
            assert expected_key in all_keys

        # Should not have duplicates
        assert len(all_keys) == len(set(all_keys))

    def test_language_consistency_across_methods(self):
        """Test consistency across all language configuration methods."""
        test_languages = ["english", "french", "italian", "german", "en", "fr", "it", "de"]

        for lang in test_languages:
            # All methods should work without errors
            assert LanguageConfig.validate_language(lang) is True
            normalized = LanguageConfig.normalize_language(lang)
            info = LanguageConfig.get_language_info(lang)
            name = LanguageConfig.get_language_name(lang)
            code = LanguageConfig.get_language_code(lang)
            prompt_key = LanguageConfig.get_prompt_key(lang)

            # Check consistency
            assert info.name == name
            assert info.code == code
            assert info.prompt_key == prompt_key

            # Normalized language should also work with all methods
            assert LanguageConfig.validate_language(normalized) is True
            normalized_info = LanguageConfig.get_language_info(normalized)
            assert normalized_info.name == name
            assert normalized_info.code == code
            assert normalized_info.prompt_key == prompt_key

    def test_case_insensitive_consistency(self):
        """Test that case insensitive operations are consistent."""
        case_variations = [
            ("english", ["ENGLISH", "English", "eNgLiSh"]),
            ("french", ["FRENCH", "French", "fReNcH"]),
            ("italian", ["ITALIAN", "Italian", "iTaLiAn"]),
            ("german", ["GERMAN", "German", "gErMaN"]),
            ("en", ["EN", "En", "eN"]),
            ("fr", ["FR", "Fr", "fR"]),
            ("it", ["IT", "It", "iT"]),
            ("de", ["DE", "De", "dE"]),
        ]

        for base_lang, variations in case_variations:
            base_info = LanguageConfig.get_language_info(base_lang)

            for variation in variations:
                # All variations should normalize to the same base
                assert LanguageConfig.normalize_language(variation) == base_lang

                # All variations should return the same info
                var_info = LanguageConfig.get_language_info(variation)
                assert var_info.name == base_info.name
                assert var_info.code == base_info.code
                assert var_info.prompt_key == base_info.prompt_key

    def test_boundary_conditions(self):
        """Test boundary conditions and edge cases."""
        # Very long strings
        long_invalid = "a" * 1000
        assert LanguageConfig.validate_language(long_invalid) is False
        with pytest.raises(LanguageValidationError):
            LanguageConfig.normalize_language(long_invalid)

        # Mixed case with whitespace
        mixed_cases = [
            "  ENGLISH  ",
            "\t French \n",
            " \t ITALIAN \n ",
            "  german  ",
        ]

        for mixed_case in mixed_cases:
            assert LanguageConfig.validate_language(mixed_case) is True
            normalized = LanguageConfig.normalize_language(mixed_case)
            assert normalized in ["english", "french", "italian", "german"]

        # Unicode characters (should be invalid)
        unicode_inputs = ["français", "italiano", "deutsch", "inglés"]
        for unicode_input in unicode_inputs:
            assert LanguageConfig.validate_language(unicode_input) is False
            with pytest.raises(LanguageValidationError):
                LanguageConfig.normalize_language(unicode_input)

    def test_performance_with_large_inputs(self):
        """Test performance with large number of validation calls."""
        import time

        # Test with many valid inputs
        valid_inputs = ["english", "french", "italian", "german", "en", "fr", "it", "de"] * 100

        start_time = time.time()
        for lang in valid_inputs:
            LanguageConfig.validate_language(lang)
            LanguageConfig.normalize_language(lang)
        end_time = time.time()

        # Should complete quickly (less than 1 second for 800 operations)
        assert (end_time - start_time) < 1.0

        # Test with many invalid inputs
        invalid_inputs = ["spanish", "portuguese", "chinese", "invalid"] * 100

        start_time = time.time()
        for lang in invalid_inputs:
            LanguageConfig.validate_language(lang)
        end_time = time.time()

        # Should complete quickly even for invalid inputs
        assert (end_time - start_time) < 1.0

    def test_thread_safety_simulation(self):
        """Test that language configuration methods are thread-safe."""
        import concurrent.futures

        results = []
        errors = []

        def test_language_operations(lang):
            try:
                # Perform multiple operations
                is_valid = LanguageConfig.validate_language(lang)
                if is_valid:
                    normalized = LanguageConfig.normalize_language(lang)
                    info = LanguageConfig.get_language_info(normalized)
                    name = LanguageConfig.get_language_name(normalized)
                    code = LanguageConfig.get_language_code(normalized)
                    return (lang, normalized, info.name, name, code)
                else:
                    return (lang, None, None, None, None)
            except Exception as e:
                errors.append((lang, str(e)))
                return None

        # Test with multiple threads
        languages = ["english", "french", "italian", "german", "en", "fr", "it", "de"] * 10

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(test_language_operations, lang) for lang in languages]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Should have no errors
        assert len(errors) == 0

        # All results should be consistent
        valid_results = [r for r in results if r is not None and r[1] is not None]
        assert len(valid_results) == len(languages)

        # Check consistency of results
        for _lang, normalized, info_name, get_name, _get_code in valid_results:
            assert info_name == get_name
            assert normalized in ["english", "french", "italian", "german", "en", "fr", "it", "de"]
