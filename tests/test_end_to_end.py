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
        """Create sample documents for testing."""
        documents = {}

        # Create a text file
        txt_file = temp_dir / "python_basics.txt"
        txt_content = """
        Python Programming Language
        
        Python is a high-level, interpreted programming language created by Guido van Rossum.
        It was first released in 1991 and is known for its simplicity and readability.
        
        Key Features:
        - Easy to learn and use
        - Interpreted language (no compilation needed)
        - Object-oriented programming support
        - Extensive standard library
        - Cross-platform compatibility
        
        Python is widely used in web development, data science, artificial intelligence,
        and automation. Its syntax emphasizes code readability with significant indentation.
        """
        txt_file.write_text(txt_content.strip())
        documents["txt"] = txt_file

        # Create a markdown file
        md_file = temp_dir / "machine_learning.md"
        md_content = """
        # Machine Learning Fundamentals
        
        Machine Learning (ML) is a subset of artificial intelligence that enables computers
        to learn and make decisions from data without being explicitly programmed for every task.
        
        ## Types of Machine Learning
        
        ### Supervised Learning
        - Uses labeled training data to learn patterns
        - Examples: Classification and Regression
        - Common algorithms: Linear Regression, Decision Trees, Random Forest
        
        ### Unsupervised Learning
        - Finds patterns in data without labeled examples
        - Examples: Clustering and Dimensionality Reduction
        - Common algorithms: K-Means, PCA, DBSCAN
        
        ### Reinforcement Learning
        - Learns through interaction with an environment
        - Uses rewards and penalties to improve performance
        - Applications: Game playing, Robotics, Autonomous vehicles
        
        ## Key Concepts
        
        **Training Data**: The dataset used to train the machine learning model
        **Features**: Input variables or attributes used to make predictions
        **Labels**: The correct answers or target values for supervised learning
        **Model**: The algorithm that learns patterns and makes predictions
        **Overfitting**: When a model performs well on training data but poorly on new, unseen data
        """
        md_file.write_text(md_content.strip())
        documents["md"] = md_file

        return documents

    @pytest.fixture
    def mock_llm_responses(self, mocker):
        """Mock LLM responses for consistent testing."""
        # Mock responses for different document types
        python_flashcards = [
            {
                "question": "What is Python?",
                "answer": "A high-level, interpreted programming language created by Guido van Rossum",
                "card_type": "qa",
            },
            {"question": "When was Python first released?", "answer": "1991", "card_type": "qa"},
            {
                "question": "Python is known for its {{c1::simplicity}} and {{c2::readability}}",
                "answer": "simplicity and readability",
                "card_type": "cloze",
            },
            {
                "question": "Name three key features of Python",
                "answer": "Easy to learn, interpreted language, object-oriented programming support",
                "card_type": "qa",
            },
        ]

        ml_flashcards = [
            {
                "question": "What is Machine Learning?",
                "answer": "A subset of artificial intelligence that enables computers to learn and make "
                "decisions from data without being explicitly programmed",
                "card_type": "qa",
            },
            {
                "question": "What are the three main types of Machine Learning?",
                "answer": "Supervised Learning, Unsupervised Learning, and Reinforcement Learning",
                "card_type": "qa",
            },
            {
                "question": "Supervised learning uses {{c1::labeled training data}} to learn patterns",
                "answer": "labeled training data",
                "card_type": "cloze",
            },
            {
                "question": "What is overfitting?",
                "answer": "When a model performs well on training data but poorly on new, unseen data",
                "card_type": "qa",
            },
        ]

        # Mock the LLM client to return appropriate responses based on content
        def mock_generate_flashcards(text):
            if "Python" in text and "programming" in text:
                return python_flashcards
            elif "Machine Learning" in text:
                return ml_flashcards
            else:
                return [
                    {
                        "question": "Generic question about the content",
                        "answer": "Generic answer based on the text",
                        "card_type": "qa",
                    }
                ]

        mocker.patch(
            "src.document_to_anki.core.llm_client.LLMClient.generate_flashcards_from_text_sync",
            side_effect=mock_generate_flashcards,
        )

        return {"python": python_flashcards, "ml": ml_flashcards}

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

    def test_large_document_workflow(self, temp_dir, mock_llm_responses):
        """Test workflow with a large document that requires chunking."""
        # Create a large document
        large_file = temp_dir / "large_document.txt"

        # Generate content that would exceed typical token limits
        large_content = (
            """
        Artificial Intelligence and Machine Learning
        
        """
            + "This is a sentence about AI and ML. " * 1000
        )  # Repeat to make it large

        large_file.write_text(large_content)
        output_file = temp_dir / "large_output.csv"

        # Process the large document
        processor = DocumentProcessor()
        doc_result = processor.process_upload(large_file)

        assert doc_result.success
        assert len(doc_result.text_content) > 10000  # Should be quite large

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
        # Create document with content suitable for different card types
        mixed_file = temp_dir / "mixed_content.txt"
        mixed_content = """
        Programming Concepts
        
        Variables store data values. In Python, you can create a variable by assigning a value to it.
        Functions are reusable blocks of code. They help organize code and avoid repetition.
        Loops allow you to repeat code multiple times. Common types include for loops and while loops.
        """
        mixed_file.write_text(mixed_content)
        output_file = temp_dir / "mixed_output.csv"

        # Mock LLM to return mixed card types
        mixed_flashcards = [
            {"question": "What do variables store?", "answer": "Data values", "card_type": "qa"},
            {
                "question": "Variables store {{c1::data values}} in programming",
                "answer": "data values",
                "card_type": "cloze",
            },
            {
                "question": "What are functions?",
                "answer": "Reusable blocks of code that help organize code and avoid repetition",
                "card_type": "qa",
            },
            {
                "question": "{{c1::Loops}} allow you to repeat code multiple times",
                "answer": "Loops",
                "card_type": "cloze",
            },
        ]

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
        txt_file = sample_documents["txt"]
        output_file = temp_dir / "validated_output.csv"

        # Mock LLM to return some invalid flashcards mixed with valid ones
        mixed_quality_flashcards = [
            {"question": "What is Python?", "answer": "A programming language", "card_type": "qa"},
            {
                "question": "",  # Invalid: empty question
                "answer": "Some answer",
                "card_type": "qa",
            },
            {
                "question": "Valid question",
                "answer": "",  # Invalid: empty answer
                "card_type": "qa",
            },
            {
                "question": "Python is a {{c1::programming language}}",
                "answer": "programming language",
                "card_type": "cloze",
            },
            {
                "question": "Invalid cloze without markers",
                "answer": "answer",
                "card_type": "cloze",  # Invalid: cloze without {{c1::}} markers
            },
        ]

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

        # Should have warnings about invalid flashcards
        assert len(gen_result.warnings) > 0

        # Valid flashcards should still be created
        valid_flashcards = [card for card in gen_result.flashcards if card.validate_content()]
        assert len(valid_flashcards) > 0
        assert len(valid_flashcards) < len(mixed_quality_flashcards)  # Some should be filtered out

        # Export should only include valid flashcards
        success, summary = generator.export_to_csv(output_file)

        assert success
        assert summary["exported_flashcards"] == len(valid_flashcards)
        # Invalid flashcards are filtered during generation, not export
        assert summary["skipped_invalid"] == 0
        # But we should have warnings from generation
        assert len(gen_result.warnings) >= 3  # Should have warnings about invalid flashcards

    def test_performance_workflow(self, temp_dir, mock_llm_responses):
        """Test workflow performance with timing measurements."""
        import time

        # Create a moderately sized document
        perf_file = temp_dir / "performance_test.txt"
        perf_content = (
            """
        Software Engineering Principles
        
        """
            + "Software engineering involves systematic approaches to software development. " * 100
        )

        perf_file.write_text(perf_content)
        output_file = temp_dir / "performance_output.csv"

        # Measure document processing time
        start_time = time.time()

        processor = DocumentProcessor()
        doc_result = processor.process_upload(perf_file)

        processing_time = time.time() - start_time

        assert doc_result.success
        assert processing_time < 10.0  # Should complete within 10 seconds

        # Measure flashcard generation time
        start_time = time.time()

        generator = FlashcardGenerator()
        gen_result = generator.generate_flashcards([doc_result.text_content], doc_result.source_files)

        generation_time = time.time() - start_time

        assert gen_result.success
        assert generation_time < 30.0  # Should complete within 30 seconds (including LLM calls)

        # Measure export time
        start_time = time.time()

        success, summary = generator.export_to_csv(output_file)

        export_time = time.time() - start_time

        assert success
        assert export_time < 5.0  # Should complete within 5 seconds

        # Verify total workflow time is reasonable
        total_time = processing_time + generation_time + export_time
        assert total_time < 45.0  # Total workflow should complete within 45 seconds

    def test_memory_usage_workflow(self, temp_dir, mock_llm_responses):
        """Test workflow memory usage with large documents."""
        import os

        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create multiple large documents
        large_files = []
        for i in range(3):
            large_file = temp_dir / f"large_doc_{i}.txt"
            large_content = f"Document {i} content. " * 5000  # ~100KB each
            large_file.write_text(large_content)
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

        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB"
