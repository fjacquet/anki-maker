"""Tests for FlashcardGenerator class."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.document_to_anki.core.flashcard_generator import FlashcardGenerationError, FlashcardGenerator
from src.document_to_anki.core.llm_client import LLMClient
from src.document_to_anki.models.flashcard import Flashcard


class TestFlashcardGenerator:
    """Test cases for FlashcardGenerator class."""

    @pytest.fixture
    def mock_llm_client(self, mocker):
        """Create a mock LLM client."""
        mock_client = mocker.Mock(spec=LLMClient)
        return mock_client

    @pytest.fixture
    def generator(self, mock_llm_client):
        """Create a FlashcardGenerator with mock LLM client."""
        return FlashcardGenerator(llm_client=mock_llm_client)

    @pytest.fixture
    def generator_with_config_mock(self, mocker):
        """Create a FlashcardGenerator with ModelConfig mocked."""
        with patch("src.document_to_anki.core.flashcard_generator.LLMClient") as mock_llm_class:
            mock_llm_instance = mocker.Mock(spec=LLMClient)
            mock_llm_instance.get_current_model.return_value = "gemini/gemini-2.5-flash"
            mock_llm_class.return_value = mock_llm_instance

            generator = FlashcardGenerator()
            generator.llm_client = mock_llm_instance
            return generator

    @pytest.fixture
    def sample_flashcard_data(self):
        """Sample flashcard data from LLM."""
        return [
            {"question": "What is the capital of France?", "answer": "Paris", "card_type": "qa"},
            {"question": "The capital of France is {{c1::Paris}}", "answer": "Paris", "card_type": "cloze"},
        ]

    @pytest.fixture
    def sample_flashcards(self):
        """Sample Flashcard objects."""
        return [
            Flashcard.create("What is Python?", "A programming language", "qa", "test.txt"),
            Flashcard.create("Python is a {{c1::programming language}}", "programming language", "cloze", "test.txt"),
        ]

    def test_init_with_llm_client(self, mock_llm_client):
        """Test initialization with provided LLM client."""
        generator = FlashcardGenerator(llm_client=mock_llm_client)
        assert generator.llm_client is mock_llm_client
        assert generator.flashcards == []

    def test_init_without_llm_client(self):
        """Test initialization without LLM client creates default one."""
        generator = FlashcardGenerator()
        assert isinstance(generator.llm_client, LLMClient)
        assert generator.flashcards == []

    def test_generate_flashcards_success(self, generator, mock_llm_client, sample_flashcard_data):
        """Test successful flashcard generation."""
        # Setup mock
        mock_llm_client.generate_flashcards_from_text_sync.return_value = sample_flashcard_data

        # Test
        text_content = ["Sample text content"]
        source_files = ["test.txt"]
        result = generator.generate_flashcards(text_content, source_files)

        # Assertions
        assert result.success
        assert len(result.flashcards) == 2
        assert result.flashcard_count == 2
        assert result.valid_flashcard_count == 2
        assert len(result.errors) == 0
        assert result.source_files == source_files

        # Check flashcards were created correctly
        flashcards = generator.flashcards
        assert len(flashcards) == 2
        assert flashcards[0].question == "What is the capital of France?"
        assert flashcards[0].answer == "Paris"
        assert flashcards[0].card_type == "qa"
        assert flashcards[0].source_file == "test.txt"

    def test_generate_flashcards_empty_content(self, generator):
        """Test flashcard generation with empty content."""
        result = generator.generate_flashcards([])

        assert not result.success
        assert len(result.flashcards) == 0
        assert len(result.errors) == 1
        assert "No text content provided" in result.errors[0]

    def test_generate_flashcards_llm_failure(self, generator, mock_llm_client):
        """Test flashcard generation when LLM fails."""
        # Setup mock to raise exception
        mock_llm_client.generate_flashcards_from_text_sync.side_effect = Exception("LLM API error")

        # Test
        text_content = ["Sample text content"]
        result = generator.generate_flashcards(text_content)

        # Assertions
        assert not result.success
        assert len(result.flashcards) == 0
        assert len(result.errors) == 1
        assert "Failed to generate flashcards from text chunk 1" in result.errors[0]

    def test_generate_flashcards_malformed_data(self, generator, mock_llm_client):
        """Test flashcard generation with malformed LLM response."""
        # Setup mock with malformed data
        malformed_data = [
            {"question": "Valid question", "answer": "Valid answer", "card_type": "qa"},
            {"question": "", "answer": "No question"},  # Missing question
            {"answer": "No question field"},  # Missing question field
        ]
        mock_llm_client.generate_flashcards_from_text_sync.return_value = malformed_data

        # Test
        result = generator.generate_flashcards(["Sample text"])

        # Should only create valid flashcards
        assert len(result.flashcards) == 1
        assert len(result.warnings) >= 1  # Should have warnings about invalid cards

    def test_preview_flashcards(self, generator, sample_flashcards):
        """Test flashcard preview functionality."""
        generator._flashcards = sample_flashcards

        preview = generator.get_flashcard_preview_text()

        assert "Flashcard Preview (2 cards)" in preview
        assert "What is Python?" in preview
        assert "A programming language" in preview
        assert "programming language" in preview

    def test_preview_flashcards_empty(self, generator):
        """Test preview with no flashcards."""
        preview = generator.get_flashcard_preview_text()
        assert preview == "No flashcards to preview."

    def test_preview_flashcards_custom_list(self, generator, sample_flashcards):
        """Test preview with custom flashcard list."""
        preview = generator.get_flashcard_preview_text(sample_flashcards[:1])

        assert "Flashcard Preview (1 cards)" in preview
        assert "What is Python?" in preview

    def test_edit_flashcard_success(self, generator, sample_flashcards):
        """Test successful flashcard editing."""
        generator._flashcards = sample_flashcards
        flashcard_id = sample_flashcards[0].id

        success, message = generator.edit_flashcard(flashcard_id, "New question", "New answer")

        assert success
        assert "updated successfully" in message
        assert generator._flashcards[0].question == "New question"
        assert generator._flashcards[0].answer == "New answer"

    def test_edit_flashcard_not_found(self, generator, sample_flashcards):
        """Test editing non-existent flashcard."""
        generator._flashcards = sample_flashcards

        success, message = generator.edit_flashcard("nonexistent-id", "New question", "New answer")

        assert not success
        assert "not found" in message

    def test_edit_flashcard_validation_failure(self, generator, sample_flashcards):
        """Test editing flashcard with invalid data."""
        generator._flashcards = sample_flashcards
        flashcard_id = sample_flashcards[0].id
        original_question = sample_flashcards[0].question

        # Try to set empty question (should fail validation)
        success, message = generator.edit_flashcard(flashcard_id, "", "New answer")

        assert not success
        assert "cannot be empty" in message
        assert generator._flashcards[0].question == original_question  # Should revert

    def test_delete_flashcard_success(self, generator, sample_flashcards):
        """Test successful flashcard deletion."""
        generator._flashcards = sample_flashcards.copy()
        flashcard_id = sample_flashcards[0].id
        original_count = len(generator._flashcards)

        success, message = generator.delete_flashcard(flashcard_id)

        assert success
        assert "Deleted flashcard" in message
        assert len(generator._flashcards) == original_count - 1
        assert flashcard_id not in [card.id for card in generator._flashcards]

    def test_delete_flashcard_not_found(self, generator, sample_flashcards):
        """Test deleting non-existent flashcard."""
        generator._flashcards = sample_flashcards
        original_count = len(generator._flashcards)

        success, message = generator.delete_flashcard("nonexistent-id")

        assert not success
        assert "not found" in message
        assert len(generator._flashcards) == original_count

    def test_add_flashcard_success(self, generator):
        """Test successful flashcard addition."""
        flashcard, message = generator.add_flashcard("Test question", "Test answer", "qa", "test.txt")

        assert flashcard is not None
        assert "Added new flashcard" in message
        assert len(generator._flashcards) == 1
        assert generator._flashcards[0].question == "Test question"
        assert generator._flashcards[0].answer == "Test answer"
        assert generator._flashcards[0].card_type == "qa"
        assert generator._flashcards[0].source_file == "test.txt"

    def test_add_flashcard_validation_failure(self, generator):
        """Test adding invalid flashcard."""
        flashcard, message = generator.add_flashcard("", "Test answer", "qa")  # Empty question

        assert flashcard is None
        assert "cannot be empty" in message
        assert len(generator._flashcards) == 0

    def test_export_to_csv_success(self, generator, sample_flashcards):
        """Test successful CSV export."""
        generator._flashcards = sample_flashcards

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.csv"
            success, summary = generator.export_to_csv(output_path)

            assert success
            assert output_path.exists()

            # Check summary data
            assert summary["total_flashcards"] == len(sample_flashcards)
            assert summary["exported_flashcards"] > 0
            assert summary["skipped_invalid"] == 0
            assert summary["qa_cards"] + summary["cloze_cards"] == summary["exported_flashcards"]
            assert summary["file_size_bytes"] > 0
            assert len(summary["errors"]) == 0

            # Check file content
            content = output_path.read_text(encoding="utf-8")
            assert "What is Python?" in content
            assert "A programming language" in content

    def test_export_to_csv_no_flashcards(self, generator):
        """Test CSV export with no flashcards."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.csv"
            success, summary = generator.export_to_csv(output_path)

            assert not success
            assert not output_path.exists()
            assert summary["total_flashcards"] == 0
            assert summary["exported_flashcards"] == 0
            assert len(summary["errors"]) > 0

    def test_export_to_csv_custom_list(self, generator, sample_flashcards):
        """Test CSV export with custom flashcard list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.csv"
            success, summary = generator.export_to_csv(output_path, sample_flashcards[:1])

            assert success
            assert output_path.exists()
            assert summary["total_flashcards"] == 1
            assert summary["exported_flashcards"] == 1

    def test_export_to_csv_summary_statistics(self, generator):
        """Test CSV export summary statistics for different card types."""
        # Create flashcards of different types
        qa_card1 = Flashcard.create("Question 1?", "Answer 1", "qa", "file1.txt")
        qa_card2 = Flashcard.create("Question 2?", "Answer 2", "qa", "file2.txt")
        cloze_card = Flashcard.create("{{c1::Python}} is a language", "Python is a language", "cloze", "file1.txt")

        generator._flashcards = [qa_card1, qa_card2, cloze_card]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.csv"
            success, summary = generator.export_to_csv(output_path)

            assert success
            assert summary["total_flashcards"] == 3
            assert summary["exported_flashcards"] == 3
            assert summary["qa_cards"] == 2
            assert summary["cloze_cards"] == 1
            assert set(summary["source_files"]) == {"file1.txt", "file2.txt"}
            assert summary["file_size_bytes"] > 0
            assert len(summary["errors"]) == 0

    def test_export_to_csv_simple_backward_compatibility(self, generator, sample_flashcards):
        """Test backward compatibility method for simple boolean return."""
        generator._flashcards = sample_flashcards

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.csv"
            success = generator.export_to_csv_simple(output_path)

            assert success
            assert output_path.exists()

    def test_get_flashcard_by_id(self, generator, sample_flashcards):
        """Test getting flashcard by ID."""
        generator._flashcards = sample_flashcards
        flashcard_id = sample_flashcards[0].id

        found_card = generator.get_flashcard_by_id(flashcard_id)

        assert found_card is not None
        assert found_card.id == flashcard_id

    def test_get_flashcard_by_id_not_found(self, generator, sample_flashcards):
        """Test getting non-existent flashcard by ID."""
        generator._flashcards = sample_flashcards

        found_card = generator.get_flashcard_by_id("nonexistent-id")

        assert found_card is None

    def test_get_flashcards_by_source(self, generator, sample_flashcards):
        """Test getting flashcards by source file."""
        generator._flashcards = sample_flashcards

        cards = generator.get_flashcards_by_source("test.txt")

        assert len(cards) == 2
        assert all(card.source_file == "test.txt" for card in cards)

    def test_get_flashcards_by_type(self, generator, sample_flashcards):
        """Test getting flashcards by type."""
        generator._flashcards = sample_flashcards

        qa_cards = generator.get_flashcards_by_type("qa")
        cloze_cards = generator.get_flashcards_by_type("cloze")

        assert len(qa_cards) == 1
        assert len(cloze_cards) == 1
        assert qa_cards[0].card_type == "qa"
        assert cloze_cards[0].card_type == "cloze"

    def test_validate_all_flashcards(self, generator, mocker):
        """Test validation of all flashcards."""
        # Create valid flashcard
        valid_card = Flashcard.create("Valid question", "Valid answer", "qa")

        # Create a mock invalid flashcard
        invalid_card = mocker.Mock(spec=Flashcard)
        invalid_card.id = "test-invalid-id"
        invalid_card.validate_content.return_value = False

        generator._flashcards = [valid_card, invalid_card]

        valid, invalid = generator.validate_all_flashcards()

        assert len(valid) == 1
        assert len(invalid) == 1
        assert valid[0].id == valid_card.id
        assert invalid[0].id == "test-invalid-id"

    def test_clear_flashcards(self, generator, sample_flashcards):
        """Test clearing all flashcards."""
        generator._flashcards = sample_flashcards

        generator.clear_flashcards()

        assert len(generator._flashcards) == 0

    def test_get_statistics(self, generator, sample_flashcards):
        """Test getting flashcard statistics."""
        generator._flashcards = sample_flashcards

        stats = generator.get_statistics()

        assert stats["total_count"] == 2
        assert stats["valid_count"] == 2
        assert stats["invalid_count"] == 0
        assert stats["qa_count"] == 1
        assert stats["cloze_count"] == 1
        assert "test.txt" in stats["source_files"]

    def test_get_statistics_empty(self, generator):
        """Test getting statistics with no flashcards."""
        stats = generator.get_statistics()

        assert stats["total_count"] == 0
        assert stats["valid_count"] == 0
        assert stats["invalid_count"] == 0
        assert stats["qa_count"] == 0
        assert stats["cloze_count"] == 0
        assert stats["source_files"] == []

    def test_batch_processing_multiple_texts(self, generator, mock_llm_client, sample_flashcard_data):
        """Test batch processing of multiple text chunks."""
        # Setup mock to return different data for each call
        mock_llm_client.generate_flashcards_from_text_sync.side_effect = [
            sample_flashcard_data[:1],  # First chunk returns 1 flashcard
            sample_flashcard_data[1:],  # Second chunk returns 1 flashcard
        ]

        text_content = ["First text chunk", "Second text chunk"]
        source_files = ["file1.txt", "file2.txt"]

        result = generator.generate_flashcards(text_content, source_files)

        assert result.success
        assert len(result.flashcards) == 2
        assert mock_llm_client.generate_flashcards_from_text_sync.call_count == 2

    def test_batch_processing_partial_failure(self, generator, mock_llm_client, sample_flashcard_data):
        """Test batch processing with partial failures."""
        # Setup mock: first call succeeds, second fails
        mock_llm_client.generate_flashcards_from_text_sync.side_effect = [
            sample_flashcard_data[:1],
            Exception("API error"),
        ]

        text_content = ["First text chunk", "Second text chunk"]

        result = generator.generate_flashcards(text_content)

        # Should have partial success
        assert len(result.flashcards) == 1  # Only first chunk succeeded
        assert len(result.errors) == 1  # One error from second chunk
        assert not result.success  # Overall failure due to errors

    def test_flashcard_generation_error_handling(self, generator, mock_llm_client):
        """Test proper error handling during flashcard generation."""
        mock_llm_client.generate_flashcards_from_text_sync.side_effect = Exception("Critical error")

        with pytest.raises(FlashcardGenerationError):
            generator._generate_flashcards_from_single_text("test text", "test.txt", 1)

    def test_get_flashcard_statistics(self, generator):
        """Test getting flashcard statistics."""
        # Create flashcards with different types and validity
        valid_qa = Flashcard.create("Valid question?", "Valid answer", "qa", "file1.txt")
        valid_cloze = Flashcard.create("{{c1::Python}} is a language", "Python is a language", "cloze", "file2.txt")

        generator._flashcards = [valid_qa, valid_cloze]

        stats = generator.get_statistics()

        assert stats["total_count"] == 2
        assert stats["qa_count"] == 1
        assert stats["cloze_count"] == 1
        assert stats["valid_count"] == 2
        assert stats["invalid_count"] == 0
        assert len(stats["source_files"]) == 2
        assert "file1.txt" in stats["source_files"]
        assert "file2.txt" in stats["source_files"]

    def test_get_flashcard_statistics_empty(self, generator):
        """Test getting statistics with no flashcards."""
        stats = generator.get_statistics()

        assert stats["total_count"] == 0
        assert stats["qa_count"] == 0
        assert stats["cloze_count"] == 0
        assert stats["valid_count"] == 0
        assert stats["invalid_count"] == 0
        assert len(stats["source_files"]) == 0
