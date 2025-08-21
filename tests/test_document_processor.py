"""Tests for DocumentProcessor class."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.document_to_anki.core.document_processor import (
    DocumentProcessingError,
    DocumentProcessingResult,
    DocumentProcessor,
)
from src.document_to_anki.utils.text_extractor import TextExtractionError


class TestDocumentProcessor:
    """Test cases for DocumentProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()

    def test_init(self):
        """Test DocumentProcessor initialization."""
        assert self.processor.file_handler is not None
        assert self.processor.text_extractor is not None
        assert self.processor.logger is not None

    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.processor.get_supported_formats()
        assert isinstance(formats, set)
        assert ".pdf" in formats
        assert ".docx" in formats
        assert ".txt" in formats
        assert ".md" in formats

    @patch("src.document_to_anki.core.document_processor.Path.exists")
    def test_process_upload_nonexistent_path(self, mock_exists):
        """Test processing non-existent path raises error."""
        mock_exists.return_value = False
        
        with pytest.raises(DocumentProcessingError, match="Upload path does not exist"):
            self.processor.process_upload("/nonexistent/path")

    @patch("src.document_to_anki.core.document_processor.Path.is_file")
    @patch("src.document_to_anki.core.document_processor.Path.exists")
    def test_process_upload_single_file_success(self, mock_exists, mock_is_file):
        """Test successful processing of a single file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Mock file handler and text extractor
        with patch.object(self.processor.file_handler, 'validate_file_type', return_value=True), \
             patch.object(self.processor.text_extractor, 'extract_text', return_value="Sample text content"):
            
            result = self.processor.process_upload("test.txt")
            
            assert isinstance(result, DocumentProcessingResult)
            assert result.text_content == "Sample text content"
            assert result.file_count == 1
            assert result.total_characters == len("Sample text content")
            assert result.success

    @patch("src.document_to_anki.core.document_processor.Path.is_file")
    @patch("src.document_to_anki.core.document_processor.Path.exists")
    def test_process_upload_file_validation_failure(self, mock_exists, mock_is_file):
        """Test processing file that fails validation."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        with patch.object(self.processor.file_handler, 'validate_file_type', return_value=False):
            with pytest.raises(DocumentProcessingError, match="Unsupported file type"):
                self.processor.process_upload("test.xyz")

    @patch("src.document_to_anki.core.document_processor.Path.is_file")
    @patch("src.document_to_anki.core.document_processor.Path.exists")
    def test_process_upload_text_extraction_failure(self, mock_exists, mock_is_file):
        """Test processing when text extraction fails."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        with patch.object(self.processor.file_handler, 'validate_file_type', return_value=True), \
             patch.object(self.processor.text_extractor, 'extract_text', 
                         side_effect=TextExtractionError("Extraction failed")):
            
            with pytest.raises(DocumentProcessingError, match="Unexpected error during document processing"):
                self.processor.process_upload("test.txt")

    @patch("src.document_to_anki.core.document_processor.Path.is_dir")
    @patch("src.document_to_anki.core.document_processor.Path.is_file")
    @patch("src.document_to_anki.core.document_processor.Path.exists")
    def test_process_upload_folder_success(self, mock_exists, mock_is_file, mock_is_dir):
        """Test successful processing of a folder."""
        mock_exists.return_value = True
        mock_is_file.return_value = False
        mock_is_dir.return_value = True
        
        # Mock folder processing
        mock_file_paths = [Path("file1.txt"), Path("file2.txt")]
        with patch.object(self.processor.file_handler, 'process_folder', return_value=mock_file_paths), \
             patch.object(self.processor.text_extractor, 'extract_text', 
                         side_effect=["Content 1", "Content 2"]):
            
            result = self.processor.process_upload("/test/folder")
            
            assert isinstance(result, DocumentProcessingResult)
            assert result.file_count == 2
            assert "Content 1" in result.text_content
            assert "Content 2" in result.text_content
            assert result.success

    def test_consolidate_texts_single_file(self):
        """Test text consolidation for single file."""
        texts = ["Single file content"]
        file_paths = [Path("test.txt")]
        
        result = self.processor._consolidate_texts(texts, file_paths)
        assert result == "Single file content"

    def test_consolidate_texts_multiple_files(self):
        """Test text consolidation for multiple files."""
        texts = ["Content 1", "Content 2"]
        file_paths = [Path("file1.txt"), Path("file2.txt")]
        
        result = self.processor._consolidate_texts(texts, file_paths)
        
        assert "Content 1" in result
        assert "Content 2" in result
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "=" in result  # Check for separators

    def test_consolidate_texts_empty_list(self):
        """Test text consolidation with empty list raises error."""
        with pytest.raises(DocumentProcessingError, match="No text content to consolidate"):
            self.processor._consolidate_texts([], [])

    def test_validate_upload_path_nonexistent(self):
        """Test validation of non-existent path."""
        result = self.processor.validate_upload_path("/nonexistent/path")
        assert result is False

    @patch("src.document_to_anki.core.document_processor.Path.is_file")
    @patch("src.document_to_anki.core.document_processor.Path.exists")
    def test_validate_upload_path_valid_file(self, mock_exists, mock_is_file):
        """Test validation of valid file path."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        with patch.object(self.processor.file_handler, 'validate_file_type', return_value=True):
            result = self.processor.validate_upload_path("test.txt")
            assert result is True


class TestDocumentProcessingResult:
    """Test cases for DocumentProcessingResult."""

    def test_init(self):
        """Test DocumentProcessingResult initialization."""
        result = DocumentProcessingResult(
            text_content="Test content",
            source_files=["test.txt"],
            file_count=1,
            total_characters=12
        )
        
        assert result.text_content == "Test content"
        assert result.source_files == ["test.txt"]
        assert result.file_count == 1
        assert result.total_characters == 12
        assert result.errors == []
        assert result.warnings == []

    def test_success_property(self):
        """Test success property."""
        result = DocumentProcessingResult(
            text_content="Test",
            source_files=["test.txt"],
            file_count=1,
            total_characters=4
        )
        
        assert result.success is True
        
        result.add_error("Test error")
        assert result.success is False

    def test_add_error(self):
        """Test adding error."""
        result = DocumentProcessingResult(
            text_content="Test",
            source_files=["test.txt"],
            file_count=1,
            total_characters=4
        )
        
        result.add_error("Test error")
        assert "Test error" in result.errors

    def test_add_warning(self):
        """Test adding warning."""
        result = DocumentProcessingResult(
            text_content="Test",
            source_files=["test.txt"],
            file_count=1,
            total_characters=4
        )
        
        result.add_warning("Test warning")
        assert "Test warning" in result.warnings

    def test_get_summary(self):
        """Test getting summary."""
        result = DocumentProcessingResult(
            text_content="Test content",
            source_files=["test.txt"],
            file_count=1,
            total_characters=12
        )
        
        summary = result.get_summary()
        assert "Document processing completed" in summary
        assert "Processed 1 files" in summary
        assert "Extracted 12 characters" in summary
        assert "test.txt" in summary