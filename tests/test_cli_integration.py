"""
Integration tests for CLI functionality.

Tests the complete CLI workflow from document processing to CSV export.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src.document_to_anki.cli.main import main
from src.document_to_anki.core.document_processor import DocumentProcessingResult
from src.document_to_anki.models.flashcard import Flashcard, ProcessingResult


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    @pytest.fixture(autouse=True)
    def mock_model_config(self, mocker):
        """Mock ModelConfig for all CLI tests."""
        with patch("src.document_to_anki.cli.main.ModelConfig") as mock_config:
            mock_config.validate_and_get_model.return_value = "gemini/gemini-2.5-flash"
            mock_config.get_model_from_env.return_value = "gemini/gemini-2.5-flash"
            mock_config.validate_model_config.return_value = True
            mock_config.SUPPORTED_MODELS = {"gemini/gemini-2.5-flash": "GEMINI_API_KEY"}
            mock_config.get_supported_models.return_value = ["gemini/gemini-2.5-flash"]
            yield mock_config

    @pytest.fixture
    def sample_txt_file(self, tmp_path):
        """Create a sample text file for testing."""
        content = """
        Python Programming
        
        Python is a programming language. It was created by Guido van Rossum.
        Python is known for its simplicity and readability.
        """
        file_path = tmp_path / "sample.txt"
        file_path.write_text(content)
        return file_path

    @pytest.fixture
    def sample_md_file(self, tmp_path):
        """Create a sample markdown file for testing."""
        content = """
        # Machine Learning
        
        Machine Learning is a subset of AI. It enables computers to learn from data.
        Common algorithms include Linear Regression and Decision Trees.
        """
        file_path = tmp_path / "sample.md"
        file_path.write_text(content)
        return file_path

    @pytest.fixture
    def mock_successful_processing(self, mocker):
        """Mock successful document processing and flashcard generation."""
        # Mock document processing
        mock_doc_result = DocumentProcessingResult(
            text_content="Sample text content for testing",
            source_files=["sample.txt"],
            file_count=1,
            total_characters=35,
        )
        mocker.patch(
            "src.document_to_anki.core.document_processor.DocumentProcessor.process_upload",
            return_value=mock_doc_result,
        )

        # Mock flashcard generation
        sample_flashcards = [
            Flashcard.create("What is Python?", "A programming language", "qa", "sample.txt"),
            Flashcard.create("Who created Python?", "Guido van Rossum", "qa", "sample.txt"),
        ]

        mock_gen_result = ProcessingResult(
            flashcards=sample_flashcards,
            source_files=["sample.txt"],
            processing_time=1.5,
            errors=[],
            warnings=[],
        )

        mocker.patch(
            "src.document_to_anki.core.flashcard_generator.FlashcardGenerator.generate_flashcards",
            return_value=mock_gen_result,
        )

        # Mock CSV export
        mocker.patch(
            "src.document_to_anki.core.flashcard_generator.FlashcardGenerator.export_to_csv",
            return_value=(
                True,
                {
                    "total_flashcards": 2,
                    "exported_flashcards": 2,
                    "skipped_invalid": 0,
                    "qa_cards": 2,
                    "cloze_cards": 0,
                    "file_size_bytes": 150,
                    "output_path": "test_output.csv",
                    "errors": [],
                },
            ),
        )

        return sample_flashcards

    def test_cli_help_command(self, runner):
        """Test that CLI help command works."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Document to Anki CLI" in result.output
        assert "Convert documents into Anki flashcards" in result.output

    def test_cli_version_command(self, runner):
        """Test that CLI version command works."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "Document to Anki CLI v0.1.0" in result.output

    def test_convert_command_help(self, runner):
        """Test convert command help."""
        result = runner.invoke(main, ["convert", "--help"])

        assert result.exit_code == 0
        assert "Convert documents to Anki flashcards" in result.output
        assert "INPUT_PATH" in result.output

    def test_convert_nonexistent_file(self, runner):
        """Test convert command with non-existent file."""
        result = runner.invoke(main, ["convert", "/nonexistent/file.txt"])

        assert result.exit_code == 2  # Click error for invalid path
        assert "does not exist" in result.output

    def test_convert_unsupported_file_type(self, runner, tmp_path):
        """Test convert command with unsupported file type."""
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("Some content")

        result = runner.invoke(main, ["convert", str(unsupported_file)])

        assert result.exit_code == 1
        assert "Invalid input path" in result.output
        assert "Unsupported file format" in result.output

    def test_convert_single_file_batch_mode(self, runner, sample_txt_file, tmp_path, mock_successful_processing):
        """Test converting a single file in batch mode (no interactive prompts)."""
        output_file = tmp_path / "output.csv"

        result = runner.invoke(
            main, ["convert", str(sample_txt_file), "--output", str(output_file), "--batch", "--no-preview"]
        )

        assert result.exit_code == 0
        assert "Processing:" in result.output
        assert "Step 1: Processing documents" in result.output
        assert "Step 2: Generating flashcards" in result.output
        assert "Step 4: Exporting to CSV" in result.output
        assert "Conversion completed successfully" in result.output

    def test_convert_single_file_with_preview_skip(self, runner, sample_txt_file, tmp_path, mock_successful_processing):
        """Test converting a single file with preview skipped."""
        output_file = tmp_path / "output.csv"

        result = runner.invoke(
            main, ["convert", str(sample_txt_file), "--output", str(output_file), "--no-preview", "--batch"]
        )

        assert result.exit_code == 0
        assert "Step 3: Review and edit flashcards" not in result.output
        assert "Conversion completed successfully" in result.output

    def test_convert_with_interactive_continue(self, runner, sample_txt_file, tmp_path, mock_successful_processing):
        """Test convert with interactive mode - continue to export."""
        output_file = tmp_path / "output.csv"

        # Simulate user choosing 'c' (continue) in interactive mode
        result = runner.invoke(
            main, ["convert", str(sample_txt_file), "--output", str(output_file)], input="c\ny\n"
        )  # 'c' for continue, 'y' for export confirmation

        assert result.exit_code == 0
        assert "Step 3: Review and edit flashcards" in result.output
        assert "Flashcard Management Menu" in result.output

    def test_convert_with_interactive_quit(self, runner, sample_txt_file, tmp_path, mock_successful_processing):
        """Test convert with interactive mode - quit without saving."""
        output_file = tmp_path / "output.csv"

        # Simulate user choosing 'q' (quit) in interactive mode
        result = runner.invoke(
            main, ["convert", str(sample_txt_file), "--output", str(output_file)], input="q\n"
        )  # 'q' for quit

        assert result.exit_code == 0
        assert "Exiting without saving" in result.output

    def test_convert_document_processing_error(self, runner, sample_txt_file, tmp_path, mocker):
        """Test convert command when document processing fails."""
        # Mock document processing failure
        from src.document_to_anki.core.document_processor import DocumentProcessingError

        mocker.patch(
            "src.document_to_anki.core.document_processor.DocumentProcessor.process_upload",
            side_effect=DocumentProcessingError("Failed to process document"),
        )

        result = runner.invoke(main, ["convert", str(sample_txt_file), "--batch"])

        assert result.exit_code == 1
        assert "Document processing failed" in result.output
        assert "Troubleshooting tips" in result.output

    def test_convert_flashcard_generation_error(self, runner, sample_txt_file, tmp_path, mocker):
        """Test convert command when flashcard generation fails."""
        # Mock successful document processing
        mock_doc_result = DocumentProcessingResult(
            text_content="Sample text", source_files=["sample.txt"], file_count=1, total_characters=11
        )
        mocker.patch(
            "src.document_to_anki.core.document_processor.DocumentProcessor.process_upload",
            return_value=mock_doc_result,
        )

        # Mock flashcard generation failure
        from src.document_to_anki.core.flashcard_generator import FlashcardGenerationError

        mocker.patch(
            "src.document_to_anki.core.flashcard_generator.FlashcardGenerator.generate_flashcards",
            side_effect=FlashcardGenerationError("API error"),
        )

        result = runner.invoke(main, ["convert", str(sample_txt_file), "--batch"])

        assert result.exit_code == 1
        assert "Flashcard generation failed" in result.output
        assert "Troubleshooting tips" in result.output

    def test_batch_convert_command_help(self, runner):
        """Test batch-convert command help."""
        result = runner.invoke(main, ["batch-convert", "--help"])

        assert result.exit_code == 0
        assert "Convert multiple documents" in result.output
        assert "INPUT_PATHS" in result.output

    def test_batch_convert_no_inputs(self, runner):
        """Test batch-convert with no input paths."""
        result = runner.invoke(main, ["batch-convert"])

        # Click returns exit code 2 for usage errors (missing required arguments)
        assert result.exit_code == 2
        assert "Missing argument" in result.output or "No input paths provided" in result.output

    def test_batch_convert_multiple_files(
        self, runner, sample_txt_file, sample_md_file, tmp_path, mock_successful_processing
    ):
        """Test batch converting multiple files."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            main,
            [
                "batch-convert",
                str(sample_txt_file),
                str(sample_md_file),
                "--output-dir",
                str(output_dir),
                "--batch",
            ],
        )

        assert result.exit_code == 0
        assert "Batch processing 2 inputs" in result.output
        assert "Batch Processing Summary" in result.output
        assert "Successful: 2" in result.output

    def test_batch_convert_with_failures(self, runner, sample_txt_file, tmp_path, mocker):
        """Test batch convert with some failures."""
        # Create an invalid file
        invalid_file = tmp_path / "invalid.xyz"
        invalid_file.write_text("content")

        output_dir = tmp_path / "output"

        # Mock validation to fail for invalid file

        def mock_validate(path):
            if path.suffix == ".xyz":
                return False
            return True

        mocker.patch(
            "src.document_to_anki.core.document_processor.DocumentProcessor.validate_upload_path",
            side_effect=mock_validate,
        )

        result = runner.invoke(
            main,
            [
                "batch-convert",
                str(sample_txt_file),
                str(invalid_file),
                "--output-dir",
                str(output_dir),
                "--batch",
            ],
        )

        assert result.exit_code == 1  # Exit with error due to failures
        assert "Failed: 1" in result.output

    def test_convert_keyboard_interrupt(self, runner, sample_txt_file, tmp_path, mocker):
        """Test handling of keyboard interrupt during conversion."""
        # Mock document processing to raise KeyboardInterrupt
        mocker.patch(
            "src.document_to_anki.core.document_processor.DocumentProcessor.process_upload",
            side_effect=KeyboardInterrupt(),
        )

        result = runner.invoke(main, ["convert", str(sample_txt_file), "--batch"])

        assert result.exit_code == 1
        assert "Operation cancelled by user" in result.output

    def test_convert_unexpected_error(self, runner, sample_txt_file, tmp_path, mocker):
        """Test handling of unexpected errors during conversion."""
        # Mock document processing to raise unexpected error
        mocker.patch(
            "src.document_to_anki.core.document_processor.DocumentProcessor.process_upload",
            side_effect=RuntimeError("Unexpected error"),
        )

        result = runner.invoke(main, ["convert", str(sample_txt_file), "--batch"])

        assert result.exit_code == 1
        assert "Unexpected error" in result.output
        assert "General troubleshooting" in result.output

    def test_convert_permission_error_on_export(
        self, runner, sample_txt_file, tmp_path, mock_successful_processing, mocker
    ):
        """Test handling of permission error during CSV export."""
        # Mock CSV export to raise PermissionError
        mocker.patch(
            "src.document_to_anki.core.flashcard_generator.FlashcardGenerator.export_to_csv",
            side_effect=PermissionError("Permission denied"),
        )

        result = runner.invoke(main, ["convert", str(sample_txt_file), "--batch"])

        assert result.exit_code == 1
        assert "Permission denied" in result.output
        assert "Solutions:" in result.output

    def test_convert_with_verbose_logging(self, runner, sample_txt_file, tmp_path, mock_successful_processing):
        """Test convert command with verbose logging enabled."""
        output_file = tmp_path / "output.csv"

        result = runner.invoke(
            main, ["--verbose", "convert", str(sample_txt_file), "--output", str(output_file), "--batch"]
        )

        assert result.exit_code == 0
        # Verbose mode should show more detailed logging
        # The exact format depends on loguru configuration

    def test_convert_folder_input(self, runner, tmp_path, mock_successful_processing):
        """Test converting a folder containing multiple files."""
        # Create a folder with multiple files
        folder = tmp_path / "documents"
        folder.mkdir()

        (folder / "doc1.txt").write_text("Python is a programming language.")
        (folder / "doc2.md").write_text("# Machine Learning\nML is a subset of AI.")

        output_file = tmp_path / "output.csv"

        result = runner.invoke(main, ["convert", str(folder), "--output", str(output_file), "--batch"])

        assert result.exit_code == 0
        assert "Processing:" in result.output

    def test_convert_default_output_path(self, runner, sample_txt_file, mock_successful_processing):
        """Test convert command with default output path generation."""
        result = runner.invoke(main, ["convert", str(sample_txt_file), "--batch"])

        assert result.exit_code == 0
        # Should generate default output path based on input file name
        expected_output = sample_txt_file.parent / f"{sample_txt_file.stem}_flashcards.csv"
        assert str(expected_output) in result.output or "flashcards.csv" in result.output


class TestCLIInteractiveFeatures:
    """Test CLI interactive features with mocked user input."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_file_with_flashcards(self, tmp_path, mocker):
        """Create a sample file and mock flashcard generation."""
        file_path = tmp_path / "sample.txt"
        file_path.write_text("Python is a programming language.")

        # Mock document processing
        mock_doc_result = DocumentProcessingResult(
            text_content="Python is a programming language.",
            source_files=["sample.txt"],
            file_count=1,
            total_characters=35,
        )
        mocker.patch(
            "src.document_to_anki.core.document_processor.DocumentProcessor.process_upload",
            return_value=mock_doc_result,
        )

        # Create sample flashcards
        sample_flashcards = [
            Flashcard.create("What is Python?", "A programming language", "qa", "sample.txt"),
            Flashcard.create("Python is a {{c1::programming language}}", "programming language", "cloze", "sample.txt"),
        ]

        mock_gen_result = ProcessingResult(
            flashcards=sample_flashcards,
            source_files=["sample.txt"],
            processing_time=1.5,
            errors=[],
            warnings=[],
        )

        # Mock the flashcard generator to return our sample flashcards
        mock_generator = mocker.patch("src.document_to_anki.core.flashcard_generator.FlashcardGenerator")
        mock_generator_instance = mock_generator.return_value
        mock_generator_instance.generate_flashcards.return_value = mock_gen_result
        mock_generator_instance.flashcards = sample_flashcards
        mock_generator_instance.preview_flashcards.return_value = None
        mock_generator_instance.export_to_csv.return_value = (
            True,
            {
                "total_flashcards": 2,
                "exported_flashcards": 2,
                "skipped_invalid": 0,
                "qa_cards": 1,
                "cloze_cards": 1,
                "file_size_bytes": 150,
                "output_path": "test_output.csv",
                "errors": [],
            },
        )

        return file_path, sample_flashcards

    def test_interactive_edit_flashcard(self, runner, sample_file_with_flashcards, tmp_path):
        """Test interactive flashcard editing."""
        file_path, sample_flashcards = sample_file_with_flashcards
        output_file = tmp_path / "output.csv"

        # Simulate: edit (e) -> select card 1 -> proceed -> new question -> new answer -> save -> continue (c) -> export (y)  # noqa: E501
        user_input = "e\n1\ny\nWhat is Python programming?\nA high-level programming language\ny\nc\ny\n"

        result = runner.invoke(main, ["convert", str(file_path), "--output", str(output_file)], input=user_input)

        assert result.exit_code == 0
        assert "Flashcard Management Menu" in result.output

    def test_interactive_delete_flashcard(self, runner, sample_file_with_flashcards, tmp_path):
        """Test interactive flashcard deletion."""
        file_path, sample_flashcards = sample_file_with_flashcards
        output_file = tmp_path / "output.csv"

        # Simulate: delete (d) -> select card 1 -> confirm -> final confirm -> continue (c) -> export (y)
        user_input = "d\n1\ny\ny\nc\ny\n"

        result = runner.invoke(main, ["convert", str(file_path), "--output", str(output_file)], input=user_input)

        assert result.exit_code == 0
        assert "Flashcard Management Menu" in result.output

    def test_interactive_add_flashcard(self, runner, sample_file_with_flashcards, tmp_path):
        """Test interactive flashcard addition."""
        file_path, sample_flashcards = sample_file_with_flashcards
        output_file = tmp_path / "output.csv"

        # Simulate: add (a) -> type -> question -> answer -> confirm -> continue (c) -> export (y)
        user_input = "a\nqa\nWhat is machine learning?\nA subset of AI\ny\nc\ny\n"

        result = runner.invoke(main, ["convert", str(file_path), "--output", str(output_file)], input=user_input)

        assert result.exit_code == 0
        assert "Flashcard Management Menu" in result.output

    def test_interactive_preview_flashcards(self, runner, sample_file_with_flashcards, tmp_path):
        """Test interactive flashcard preview."""
        file_path, sample_flashcards = sample_file_with_flashcards
        output_file = tmp_path / "output.csv"

        # Simulate: preview (p) -> continue (c) -> export (y)
        user_input = "p\nc\ny\n"

        result = runner.invoke(main, ["convert", str(file_path), "--output", str(output_file)], input=user_input)

        assert result.exit_code == 0
        assert "Flashcard Management Menu" in result.output

    def test_interactive_show_statistics(self, runner, sample_file_with_flashcards, tmp_path):
        """Test interactive statistics display."""
        file_path, sample_flashcards = sample_file_with_flashcards
        output_file = tmp_path / "output.csv"

        # Simulate: statistics (s) -> continue (c) -> export (y)
        user_input = "s\nc\ny\n"

        result = runner.invoke(main, ["convert", str(file_path), "--output", str(output_file)], input=user_input)

        assert result.exit_code == 0
        assert "Flashcard Management Menu" in result.output

    def test_interactive_cancel_export(self, runner, sample_file_with_flashcards, tmp_path):
        """Test canceling export in interactive mode."""
        file_path, sample_flashcards = sample_file_with_flashcards
        output_file = tmp_path / "output.csv"

        # Simulate: continue (c) -> cancel export (n)
        user_input = "c\nn\n"

        result = runner.invoke(main, ["convert", str(file_path), "--output", str(output_file)], input=user_input)

        assert result.exit_code == 0
        assert "Export cancelled by user" in result.output
