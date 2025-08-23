"""
Unit tests for prompt template generation functionality.

Tests the PromptTemplates class to ensure proper generation of language-specific
prompt templates for different content types and languages.
"""

import pytest

from src.document_to_anki.core.prompt_templates import PromptTemplates


class TestPromptTemplates:
    """Test cases for the PromptTemplates class."""

    def test_get_supported_languages(self):
        """Test that all expected languages are supported."""
        supported = PromptTemplates.get_supported_languages()
        expected = ["english", "french", "italian", "german"]

        assert supported == expected
        assert len(supported) == 4

    def test_get_supported_content_types(self):
        """Test that all expected content types are supported."""
        supported = PromptTemplates.get_supported_content_types()
        expected = ["academic", "technical", "general"]

        assert supported == expected
        assert len(supported) == 3

    def test_validate_template_parameters_valid(self):
        """Test validation with valid parameters."""
        # Test all language variations
        languages = ["english", "french", "italian", "german", "en", "fr", "it", "de"]
        content_types = ["academic", "technical", "general"]

        for lang in languages:
            for content_type in content_types:
                assert PromptTemplates.validate_template_parameters(lang, content_type)

    def test_validate_template_parameters_invalid_language(self):
        """Test validation with invalid language."""
        invalid_languages = ["spanish", "chinese", "japanese", "invalid"]

        for lang in invalid_languages:
            assert not PromptTemplates.validate_template_parameters(lang, "general")

    def test_validate_template_parameters_invalid_content_type(self):
        """Test validation with invalid content type."""
        invalid_types = ["scientific", "business", "invalid", ""]

        for content_type in invalid_types:
            assert not PromptTemplates.validate_template_parameters("english", content_type)

    def test_validate_template_parameters_case_insensitive(self):
        """Test that validation is case insensitive."""
        assert PromptTemplates.validate_template_parameters("ENGLISH", "GENERAL")
        assert PromptTemplates.validate_template_parameters("French", "Academic")
        assert PromptTemplates.validate_template_parameters("italian", "TECHNICAL")

    def test_get_template_english_general(self):
        """Test English general template generation."""
        template = PromptTemplates.get_template("english", "general")

        # Check for key English template elements
        assert "You are an expert educator" in template
        assert "JSON array" in template
        assert "question" in template
        assert "answer" in template
        assert "card_type" in template
        assert "{text}" in template
        assert "Use clear and accessible English" in template

    def test_get_template_english_academic(self):
        """Test English academic template generation."""
        template = PromptTemplates.get_template("english", "academic")

        # Check for academic-specific content
        assert "academic vocabulary" in template
        assert "scientific" in template
        assert "conceptual understanding" in template
        assert "theoretical frameworks" in template

    def test_get_template_english_technical(self):
        """Test English technical template generation."""
        template = PromptTemplates.get_template("english", "technical")

        # Check for technical-specific content
        assert "technical terminology" in template
        assert "processes and procedures" in template
        assert "cause-and-effect" in template
        assert "technical accuracy" in template

    def test_get_template_french_general(self):
        """Test French general template generation."""
        template = PromptTemplates.get_template("french", "general")

        # Check for key French template elements
        assert "Vous êtes un expert" in template
        assert "tableau JSON" in template
        assert "question" in template
        assert "answer" in template
        assert "card_type" in template
        assert "{text}" in template
        assert "français accessible et clair" in template
        assert "EN FRANÇAIS" in template

    def test_get_template_french_academic(self):
        """Test French academic template generation."""
        template = PromptTemplates.get_template("french", "academic")

        # Check for French academic-specific content
        assert "vocabulaire académique" in template
        assert "terminologie scientifique française" in template
        assert "compréhension conceptuelle" in template
        assert "cadres théoriques" in template

    def test_get_template_italian_general(self):
        """Test Italian general template generation."""
        template = PromptTemplates.get_template("italian", "general")

        # Check for key Italian template elements
        assert "Sei un esperto" in template
        assert "array JSON" in template
        assert "question" in template
        assert "answer" in template
        assert "card_type" in template
        assert "{text}" in template
        assert "italiano accessibile e chiaro" in template
        assert "IN ITALIANO" in template

    def test_get_template_italian_technical(self):
        """Test Italian technical template generation."""
        template = PromptTemplates.get_template("italian", "technical")

        # Check for Italian technical-specific content
        assert "terminologia tecnica italiana" in template
        assert "processi e le procedure" in template
        assert "causa-effetto" in template
        assert "precisione tecnica" in template

    def test_get_template_german_general(self):
        """Test German general template generation."""
        template = PromptTemplates.get_template("german", "general")

        # Check for key German template elements
        assert "Sie sind ein Experte" in template
        assert "JSON-Array" in template
        assert "question" in template
        assert "answer" in template
        assert "card_type" in template
        assert "{text}" in template
        assert "zugängliches und klares Deutsch" in template
        assert "AUF DEUTSCH" in template

    def test_get_template_german_academic(self):
        """Test German academic template generation."""
        template = PromptTemplates.get_template("german", "academic")

        # Check for German academic-specific content
        assert "akademisches Vokabular" in template
        assert "wissenschaftliche Terminologie" in template
        assert "konzeptuelle Verständnis" in template
        assert "theoretische Rahmen" in template

    def test_get_template_with_language_codes(self):
        """Test template generation with ISO language codes."""
        # Test that language codes work the same as full names
        en_template = PromptTemplates.get_template("en", "general")
        english_template = PromptTemplates.get_template("english", "general")
        assert en_template == english_template

        fr_template = PromptTemplates.get_template("fr", "general")
        french_template = PromptTemplates.get_template("french", "general")
        assert fr_template == french_template

        it_template = PromptTemplates.get_template("it", "general")
        italian_template = PromptTemplates.get_template("italian", "general")
        assert it_template == italian_template

        de_template = PromptTemplates.get_template("de", "general")
        german_template = PromptTemplates.get_template("german", "general")
        assert de_template == german_template

    def test_get_template_case_insensitive(self):
        """Test that template generation is case insensitive."""
        template1 = PromptTemplates.get_template("ENGLISH", "GENERAL")
        template2 = PromptTemplates.get_template("english", "general")
        template3 = PromptTemplates.get_template("English", "General")

        assert template1 == template2 == template3

    def test_get_template_invalid_language(self):
        """Test that invalid language raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported language"):
            PromptTemplates.get_template("spanish", "general")

    def test_get_template_invalid_content_type(self):
        """Test that invalid content type defaults to general."""
        # The current implementation should handle invalid content types gracefully
        template = PromptTemplates.get_template("english", "invalid_type")
        general_template = PromptTemplates.get_template("english", "general")

        # Should fall back to general template
        assert template == general_template

    def test_all_templates_contain_required_elements(self):
        """Test that all templates contain required JSON formatting elements."""
        languages = ["english", "french", "italian", "german"]
        content_types = ["academic", "technical", "general"]

        required_elements = ["question", "answer", "card_type", "{text}", "JSON"]

        for lang in languages:
            for content_type in content_types:
                template = PromptTemplates.get_template(lang, content_type)

                for element in required_elements:
                    assert element in template, f"Missing '{element}' in {lang} {content_type} template"

    def test_all_templates_specify_target_language(self):
        """Test that all templates clearly specify the target language."""
        language_specifications = {
            "english": ["IN ENGLISH", "English"],
            "french": ["EN FRANÇAIS", "français"],
            "italian": ["IN ITALIANO", "italiano"],
            "german": ["AUF DEUTSCH", "Deutsch"],
        }

        content_types = ["academic", "technical", "general"]

        for lang, specs in language_specifications.items():
            for content_type in content_types:
                template = PromptTemplates.get_template(lang, content_type)

                # Check that at least one language specification is present
                found_spec = any(spec in template for spec in specs)
                assert found_spec, f"No language specification found in {lang} {content_type} template"

    def test_templates_have_proper_grammar_instructions(self):
        """Test that templates include proper grammar and vocabulary instructions."""
        grammar_keywords = {
            "english": ["grammar", "vocabulary"],
            "french": ["grammaire", "vocabulaire", "accords"],
            "italian": ["grammatica", "vocabolario", "accordi"],
            "german": ["Grammatik", "Vokabular", "Kongruenz"],
        }

        for lang, keywords in grammar_keywords.items():
            template = PromptTemplates.get_template(lang, "general")

            # Check that at least one grammar-related keyword is present
            found_keyword = any(keyword in template for keyword in keywords)
            assert found_keyword, f"No grammar instructions found in {lang} template"

    def test_templates_include_examples(self):
        """Test that all templates include example JSON output."""
        languages = ["english", "french", "italian", "german"]

        for lang in languages:
            template = PromptTemplates.get_template(lang, "general")

            # Check for example structure (different languages use different words for "example")
            example_keywords = ["EXAMPLE", "EXEMPLE", "ESEMPIO", "BEISPIEL"]
            has_example = any(keyword in template.upper() for keyword in example_keywords)
            assert has_example, f"No example keyword found in {lang} template"

            assert '"question":' in template
            assert '"answer":' in template
            assert '"card_type":' in template
