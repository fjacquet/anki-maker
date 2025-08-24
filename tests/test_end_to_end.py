"""
End-to-end integration tests for the complete document-to-CSV workflow.

Tests the entire pipeline from document upload through flashcard generation to CSV export.
"""

import csv
import tempfile
import zipfile
from pathlib import Path

import pytest

from src.document_to_anki.core.document_processor import DocumentProcessor
from src.document_to_anki.core.flashcard_generator import FlashcardGenerator


class TestEndToEndWorkflow:
    """End-to-end tests for the complete document processing workflow."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_documents(self, temp_dir):
        """Create sample documents for testing using external files."""
        from tests.fixtures.test_data_loader import test_data_loader

        documents = {}

        # Create documents from external files
        documents["txt"] = test_data_loader.create_temp_document(temp_dir, "python_basics.txt")
        documents["md"] = test_data_loader.create_temp_document(temp_dir, "machine_learning.md")

        return documents

    @pytest.fixture(autouse=True)
    def mock_llm_responses(self, mocker):
        """Mock LLM responses for consistent testing - auto-applied to all tests."""
        from tests.fixtures.test_data_loader import test_data_loader

        # Create mock function using external configuration
        mock_generate_flashcards = test_data_loader.create_mock_llm_function()

        # Mock both sync and async methods
        mocker.patch(
            "src.document_to_anki.core.llm_client.LLMClient.generate_flashcards_from_text_sync",
            side_effect=mock_generate_flashcards,
        )
        mocker.patch(
            "src.document_to_anki.core.llm_client.LLMClient.generate_flashcards_from_text",
            side_effect=lambda text: mock_generate_flashcards(text),
        )

        # Mock environment variables to avoid real API calls
        mocker.patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key", "MODEL": "gemini/gemini-2.5-flash", "MOCK_LLM_RESPONSES": "true"},
        )

        return test_data_loader.get_mock_llm_responses()

    @pytest.mark.timeout(60)
    def test_single_file_complete_workflow(self, sample_documents, mock_llm_responses, temp_dir):
        """Test complete workflow with a single text file."""
        txt_file = sample_documents["txt"]
        output_file = temp_dir / "output.csv"

        # Step 1: Document Processing
        processor = DocumentProcessor()
        doc_result = processor.process_upload(txt_file)

        assert doc_result.success
        assert doc_result.file_count == 1
        assert len(doc_result.text_content) > 0
        assert "Python" in doc_result.text_content
        assert "Guido van Rossum" in doc_result.text_content

        # Step 2: Flashcard Generation
        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        assert gen_result.success
        assert len(gen_result.flashcards) > 0

        # Verify flashcard content
        flashcards = gen_result.flashcards
        questions = [card.question for card in flashcards]
        answers = [card.answer for card in flashcards]

        assert any("Python" in q for q in questions)
        assert any("1991" in a for a in answers)

        # Step 3: CSV Export
        success, summary = generator.export_to_csv(output_file)

        assert success
        assert output_file.exists()
        assert summary["exported_flashcards"] > 0
        assert summary["total_flashcards"] == len(flashcards)

        # Step 4: Verify CSV Content
        with open(output_file, encoding="utf-8") as f:
            csv_reader = csv.reader(f)
            rows = list(csv_reader)

        assert len(rows) > 0  # Should have flashcard data

        # Check that CSV contains expected content
        csv_content = "\n".join([",".join(row) for row in rows])
        assert "Python" in csv_content
        assert "programming language" in csv_content.lower()

    @pytest.mark.timeout(60)
    def test_multiple_files_workflow(self, sample_documents, mock_llm_responses, temp_dir):
        """Test complete workflow with multiple files."""
        txt_file = sample_documents["txt"]
        md_file = sample_documents["md"]
        output_file = temp_dir / "multi_output.csv"

        # Create a folder with both files
        docs_folder = temp_dir / "documents"
        docs_folder.mkdir()

        # Copy files to the folder
        (docs_folder / "python.txt").write_text(txt_file.read_text())
        (docs_folder / "ml.md").write_text(md_file.read_text())

        # Step 1: Process folder
        processor = DocumentProcessor()
        doc_result = processor.process_upload(docs_folder)

        assert doc_result.success
        assert doc_result.file_count == 2
        assert "Python" in doc_result.text_content
        assert "Machine Learning" in doc_result.text_content

        # Step 2: Generate flashcards
        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        assert gen_result.success
        assert len(gen_result.flashcards) > 0

        # Should have flashcards from both documents
        flashcards = gen_result.flashcards
        questions = [card.question for card in flashcards]

        # Check for content from both files
        has_python_content = any("Python" in q for q in questions)
        has_ml_content = any("Machine Learning" in q or "ML" in q for q in questions)

        assert has_python_content or has_ml_content  # At least one should be present

        # Step 3: Export and verify
        success, summary = generator.export_to_csv(output_file)

        assert success
        assert output_file.exists()
        assert summary["exported_flashcards"] > 0

    @pytest.mark.timeout(60)
    def test_zip_file_workflow(self, sample_documents, mock_llm_responses, temp_dir):
        """Test complete workflow with ZIP file containing multiple documents."""
        txt_file = sample_documents["txt"]
        md_file = sample_documents["md"]
        zip_file = temp_dir / "documents.zip"
        output_file = temp_dir / "zip_output.csv"

        # Create ZIP file with documents
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.write(txt_file, "python_basics.txt")
            zf.write(md_file, "machine_learning.md")

        # Step 1: Process ZIP file
        processor = DocumentProcessor()
        doc_result = processor.process_upload(zip_file)

        assert doc_result.success
        assert doc_result.file_count == 2

        # Step 2: Generate flashcards
        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        assert gen_result.success
        assert len(gen_result.flashcards) > 0

        # Step 3: Export and verify
        success, summary = generator.export_to_csv(output_file)

        assert success
        assert output_file.exists()

    def test_flashcard_editing_workflow(self, sample_documents, mock_llm_responses, temp_dir):
        """Test workflow including flashcard editing operations."""
        txt_file = sample_documents["txt"]
        output_file = temp_dir / "edited_output.csv"

        # Process document and generate flashcards
        processor = DocumentProcessor()
        doc_result = processor.process_upload(txt_file)

        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        original_count = len(gen_result.flashcards)
        assert original_count > 0

        # Test editing a flashcard
        first_flashcard = gen_result.flashcards[0]
        success, message = generator.edit_flashcard(
            first_flashcard.id,
            "What is Python programming language?",
            "A powerful, easy-to-learn programming language",
        )

        assert success
        assert "updated successfully" in message

        # Verify the edit
        edited_flashcard = generator.get_flashcard_by_id(first_flashcard.id)
        assert edited_flashcard.question == "What is Python programming language?"
        assert edited_flashcard.answer == "A powerful, easy-to-learn programming language"

        # Test adding a new flashcard
        new_flashcard, add_message = generator.add_flashcard(
            "What does IDE stand for?", "Integrated Development Environment", "qa", "manual_addition"
        )

        assert new_flashcard is not None
        assert "Added new flashcard" in add_message
        assert len(generator.flashcards) == original_count + 1

        # Test deleting a flashcard
        success, delete_message = generator.delete_flashcard(new_flashcard.id)

        assert success
        assert "Deleted flashcard" in delete_message
        assert len(generator.flashcards) == original_count

        # Export final result
        success, summary = generator.export_to_csv(output_file)

        assert success
        assert output_file.exists()
        assert summary["exported_flashcards"] == original_count

    def test_error_recovery_workflow(self, sample_documents, temp_dir, mocker):
        """Test workflow with error conditions and recovery."""
        txt_file = sample_documents["txt"]

        # Test document processing error recovery
        processor = DocumentProcessor()

        # First, test with a non-existent file
        with pytest.raises(Exception):  # Should raise DocumentProcessingError  # noqa: B017
            processor.process_upload(temp_dir / "nonexistent.txt")

        # Then test successful processing
        doc_result = processor.process_upload(txt_file)
        assert doc_result.success

        # Test flashcard generation with LLM error
        generator = FlashcardGenerator()

        # Mock LLM to fail first, then succeed
        call_count = 0

        def mock_llm_with_failure(text):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("LLM API error")
            return [{"question": "Recovery question", "answer": "Recovery answer", "card_type": "qa"}]

        mocker.patch(
            "src.document_to_anki.core.llm_client.LLMClient.generate_flashcards_from_text_sync",
            side_effect=mock_llm_with_failure,
        )

        # First call should fail
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)
        assert not gen_result.success
        assert len(gen_result.errors) > 0

        # Second call should succeed (in a real scenario, user would retry)
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)
        assert gen_result.success
        assert len(gen_result.flashcards) > 0

    @pytest.mark.slow
    def test_large_document_workflow(self, temp_dir, mock_llm_responses):
        """Test workflow with a large document that requires chunking."""
        from tests.fixtures.test_data_loader import test_data_loader

        # Get document size configuration from external config
        size_config = test_data_loader.get_document_size_config("medium")
        repeat_count = size_config.get("repeat_count", 100)

        # Create document using external template with repetition
        large_file = test_data_loader.create_temp_document(temp_dir, "large_document.txt", repeat_count=repeat_count)
        output_file = temp_dir / "large_output.csv"

        # Process the large document
        processor = DocumentProcessor()
        doc_result = processor.process_upload(large_file)

        assert doc_result.success
        expected_min_chars = size_config.get("expected_min_chars", 1000)
        assert len(doc_result.text_content) > expected_min_chars

        # Generate flashcards (should handle chunking internally)
        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        assert gen_result.success
        assert len(gen_result.flashcards) > 0

        # Export should work normally
        success, summary = generator.export_to_csv(output_file)

        assert success
        assert output_file.exists()

    def test_different_card_types_workflow(self, temp_dir, mocker):
        """Test workflow that generates different types of flashcards."""
        from tests.fixtures.test_data_loader import test_data_loader

        # Create document using external file
        mixed_file = test_data_loader.create_temp_document(temp_dir, "mixed_content.txt")
        output_file = temp_dir / "mixed_output.csv"

        # Get mixed flashcards from external config
        responses_config = test_data_loader.get_mock_llm_responses()
        mixed_flashcards = responses_config["responses"]["programming_concepts"]["flashcards"]

        mocker.patch(
            "src.document_to_anki.core.llm_client.LLMClient.generate_flashcards_from_text_sync",
            return_value=mixed_flashcards,
        )

        # Process document
        processor = DocumentProcessor()
        doc_result = processor.process_upload(mixed_file)

        # Generate flashcards
        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        assert gen_result.success

        # Verify we have both card types
        flashcards = gen_result.flashcards
        qa_cards = [card for card in flashcards if card.card_type == "qa"]
        cloze_cards = [card for card in flashcards if card.card_type == "cloze"]

        assert len(qa_cards) > 0
        assert len(cloze_cards) > 0

        # Export and verify CSV contains both types
        success, summary = generator.export_to_csv(output_file)

        assert success
        assert summary["qa_cards"] > 0
        assert summary["cloze_cards"] > 0
        assert summary["qa_cards"] + summary["cloze_cards"] == summary["exported_flashcards"]

    def test_validation_and_quality_workflow(self, sample_documents, temp_dir, mocker):
        """Test workflow with flashcard validation and quality checks."""
        from tests.fixtures.test_data_loader import test_data_loader

        txt_file = sample_documents["txt"]
        output_file = temp_dir / "validated_output.csv"

        # Get mixed quality flashcards from external config
        responses_config = test_data_loader.get_mock_llm_responses()
        mixed_quality_flashcards = responses_config["responses"]["mixed_quality"]["flashcards"]

        mocker.patch(
            "src.document_to_anki.core.llm_client.LLMClient.generate_flashcards_from_text_sync",
            return_value=mixed_quality_flashcards,
        )

        # Process document
        processor = DocumentProcessor()
        doc_result = processor.process_upload(txt_file)

        # Generate flashcards
        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        # Get validation expectations from external config
        test_config = test_data_loader.get_test_config()
        validation_config = test_config.get("validation", {})
        expected_warnings = validation_config.get("expected_warnings_count", 3)
        min_valid_flashcards = validation_config.get("min_valid_flashcards", 1)

        # Should have warnings about invalid flashcards
        assert len(gen_result.warnings) > 0

        # Valid flashcards should still be created
        valid_flashcards = [card for card in gen_result.flashcards if card.validate_content()]
        assert len(valid_flashcards) >= min_valid_flashcards
        assert len(valid_flashcards) < len(mixed_quality_flashcards)  # Some should be filtered out

        # Export should only include valid flashcards
        success, summary = generator.export_to_csv(output_file)

        assert success
        assert summary["exported_flashcards"] == len(valid_flashcards)
        # Invalid flashcards are filtered during generation, not export
        assert summary["skipped_invalid"] == 0
        # But we should have warnings from generation
        assert len(gen_result.warnings) >= expected_warnings

    @pytest.mark.slow
    def test_performance_workflow(self, temp_dir, mock_llm_responses):
        """Test workflow performance with timing measurements."""
        import time

        from tests.fixtures.test_data_loader import test_data_loader

        # Get performance expectations from external config
        perf_config = test_data_loader.get_performance_expectations("document_processing")
        size_config = test_data_loader.get_document_size_config("small")

        # Create document using external template
        perf_file = test_data_loader.create_temp_document(
            temp_dir, "performance_test.txt", repeat_count=size_config.get("repeat_count", 20)
        )
        output_file = temp_dir / "performance_output.csv"

        # Measure document processing time
        start_time = time.time()

        processor = DocumentProcessor()
        doc_result = processor.process_upload(perf_file)

        processing_time = time.time() - start_time

        assert doc_result.success
        max_processing_time = perf_config.get("max_time_seconds", 5.0)
        assert processing_time < max_processing_time

        # Measure flashcard generation time (should be fast with mocking)
        start_time = time.time()

        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        generation_time = time.time() - start_time

        assert gen_result.success
        gen_perf_config = test_data_loader.get_performance_expectations("flashcard_generation")
        max_generation_time = gen_perf_config.get("max_time_seconds", 5.0)
        assert generation_time < max_generation_time

        # Measure export time
        start_time = time.time()

        success, summary = generator.export_to_csv(output_file)

        export_time = time.time() - start_time

        assert success
        export_perf_config = test_data_loader.get_performance_expectations("csv_export")
        max_export_time = export_perf_config.get("max_time_seconds", 2.0)
        assert export_time < max_export_time

        # Verify total workflow time is reasonable
        total_time = processing_time + generation_time + export_time
        total_perf_config = test_data_loader.get_performance_expectations("total_workflow")
        max_total_time = total_perf_config.get("max_time_seconds", 12.0)
        assert total_time < max_total_time

    @pytest.mark.slow
    def test_memory_usage_workflow(self, temp_dir, mock_llm_responses):
        """Test workflow memory usage with multiple documents."""
        import os

        import psutil

        from tests.fixtures.test_data_loader import test_data_loader

        # Get memory test configuration
        test_config = test_data_loader.get_test_config()
        memory_config = test_config.get("memory_test", {})

        document_count = memory_config.get("document_count", 3)
        repeat_count = memory_config.get("content_repeat_count", 500)
        max_memory_increase = memory_config.get("max_memory_increase_mb", 50)

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create documents using external template
        large_files = []
        for i in range(document_count):
            large_file = test_data_loader.create_temp_document(
                temp_dir, f"large_doc_{i}.txt", content=f"Document {i} content. " * repeat_count
            )
            large_files.append(large_file)

        # Process all documents
        processor = DocumentProcessor()
        generator = FlashcardGenerator()

        for large_file in large_files:
            doc_result = processor.process_upload(large_file)
            _ = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

            # Export to CSV
            output_file = temp_dir / f"output_{large_file.stem}.csv"
            success, summary = generator.export_to_csv(output_file)
            assert success

            # Clear flashcards to simulate cleanup
            generator.clear_flashcards()

        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < max_memory_increase, f"Memory usage increased by {memory_increase:.2f}MB"
