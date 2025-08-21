"""Tests for the TextExtractor class."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.document_to_anki.utils import TextExtractionError, TextExtractor


class TestTextExtractor:
    """Test cases for TextExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = TextExtractor()
    
    def test_init(self):
        """Test TextExtractor initialization."""
        extractor = TextExtractor()
        assert extractor.SUPPORTED_FORMATS == {'.pdf', '.docx', '.txt', '.md'}
        assert hasattr(extractor, 'logger')
    
    def test_is_supported_format(self):
        """Test format support checking."""
        assert self.extractor.is_supported_format(Path('test.pdf'))
        assert self.extractor.is_supported_format(Path('test.docx'))
        assert self.extractor.is_supported_format(Path('test.txt'))
        assert self.extractor.is_supported_format(Path('test.md'))
        assert not self.extractor.is_supported_format(Path('test.doc'))
        assert not self.extractor.is_supported_format(Path('test.xlsx'))
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.extractor.get_supported_formats()
        assert formats == {'.pdf', '.docx', '.txt', '.md'}
        # Ensure it returns a copy
        formats.add('.test')
        assert '.test' not in self.extractor.get_supported_formats()
    
    def test_extract_text_file_not_exists(self):
        """Test extraction from non-existent file."""
        with pytest.raises(TextExtractionError, match="File does not exist"):
            self.extractor.extract_text(Path('nonexistent.txt'))
    
    def test_extract_text_unsupported_format(self):
        """Test extraction from unsupported format."""
        with tempfile.NamedTemporaryFile(suffix='.unsupported') as tmp:
            with pytest.raises(TextExtractionError, match="Unsupported file format"):
                self.extractor.extract_text(Path(tmp.name))
    
    def test_extract_text_from_txt_success(self):
        """Test successful text extraction from TXT file."""
        test_content = "This is a test document.\nWith multiple lines."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()
            
            result = self.extractor.extract_text_from_txt(Path(tmp.name))
            assert result == test_content
        
        # Clean up
        Path(tmp.name).unlink()
    
    def test_extract_text_from_txt_empty_file(self):
        """Test extraction from empty TXT file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write("")
            tmp.flush()
            
            result = self.extractor.extract_text_from_txt(Path(tmp.name))
            assert result == ""
        
        # Clean up
        Path(tmp.name).unlink()
    
    def test_extract_text_from_txt_file_not_found(self):
        """Test extraction from non-existent TXT file."""
        with pytest.raises(TextExtractionError, match="Text file not found"):
            self.extractor.extract_text_from_txt(Path('nonexistent.txt'))
    
    def test_extract_text_from_md_alias(self):
        """Test that extract_text_from_md is an alias for extract_text_from_txt."""
        test_content = "# Markdown Test\n\nThis is markdown content."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()
            
            result = self.extractor.extract_text_from_md(Path(tmp.name))
            assert result == test_content
        
        # Clean up
        Path(tmp.name).unlink()
    
    @patch('src.document_to_anki.utils.text_extractor.pypdf.PdfReader')
    def test_extract_text_from_pdf_success(self, mock_pdf_reader):
        """Test successful PDF text extraction."""
        # Mock PDF reader
        mock_reader_instance = Mock()
        mock_reader_instance.is_encrypted = False
        mock_reader_instance.pages = [Mock(), Mock()]
        mock_reader_instance.pages[0].extract_text.return_value = "Page 1 content"
        mock_reader_instance.pages[1].extract_text.return_value = "Page 2 content"
        mock_pdf_reader.return_value = mock_reader_instance
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            result = self.extractor.extract_text_from_pdf(Path(tmp.name))
            assert result == "Page 1 content\n\nPage 2 content"
        
        # Clean up
        Path(tmp.name).unlink()
    
    @patch('src.document_to_anki.utils.text_extractor.pypdf.PdfReader')
    def test_extract_text_from_pdf_encrypted(self, mock_pdf_reader):
        """Test PDF extraction from encrypted file."""
        mock_reader_instance = Mock()
        mock_reader_instance.is_encrypted = True
        mock_pdf_reader.return_value = mock_reader_instance
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="PDF file is encrypted"):
                self.extractor.extract_text_from_pdf(Path(tmp.name))
        
        # Clean up
        Path(tmp.name).unlink()
    
    @patch('src.document_to_anki.utils.text_extractor.Document')
    def test_extract_text_from_docx_success(self, mock_document):
        """Test successful DOCX text extraction."""
        # Mock document
        mock_doc = Mock()
        mock_paragraph1 = Mock()
        mock_paragraph1.text = "First paragraph"
        mock_paragraph2 = Mock()
        mock_paragraph2.text = "Second paragraph"
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
        mock_doc.tables = []
        mock_document.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            result = self.extractor.extract_text_from_docx(Path(tmp.name))
            assert result == "First paragraph\n\nSecond paragraph"
        
        # Clean up
        Path(tmp.name).unlink()
    
    def test_extract_text_integration_txt(self):
        """Test integration of extract_text method with TXT file."""
        test_content = "Integration test content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()
            
            result = self.extractor.extract_text(Path(tmp.name))
            assert result == test_content
        
        # Clean up
        Path(tmp.name).unlink()