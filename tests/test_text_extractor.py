"""Tests for the TextExtractor class."""

import tempfile
from pathlib import Path

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
        assert extractor.SUPPORTED_FORMATS == {".pdf", ".docx", ".txt", ".md"}
        assert hasattr(extractor, "logger")

    def test_is_supported_format(self):
        """Test format support checking."""
        assert self.extractor.is_supported_format(Path("test.pdf"))
        assert self.extractor.is_supported_format(Path("test.docx"))
        assert self.extractor.is_supported_format(Path("test.txt"))
        assert self.extractor.is_supported_format(Path("test.md"))
        assert not self.extractor.is_supported_format(Path("test.doc"))
        assert not self.extractor.is_supported_format(Path("test.xlsx"))

    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.extractor.get_supported_formats()
        assert formats == {".pdf", ".docx", ".txt", ".md"}
        # Ensure it returns a copy
        formats.add(".test")
        assert ".test" not in self.extractor.get_supported_formats()

    def test_extract_text_file_not_exists(self):
        """Test extraction from non-existent file."""
        with pytest.raises(TextExtractionError, match="File does not exist"):
            self.extractor.extract_text(Path("nonexistent.txt"))

    def test_extract_text_unsupported_format(self):
        """Test extraction from unsupported format."""
        with tempfile.NamedTemporaryFile(suffix=".unsupported") as tmp:
            with pytest.raises(TextExtractionError, match="Unsupported file format"):
                self.extractor.extract_text(Path(tmp.name))

    def test_extract_text_from_txt_success(self):
        """Test successful text extraction from TXT file."""
        test_content = "This is a test document.\nWith multiple lines."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()

            result = self.extractor.extract_text_from_txt(Path(tmp.name))
            assert result == test_content

        # Clean up
        Path(tmp.name).unlink()

    def test_extract_text_from_txt_empty_file(self):
        """Test extraction from empty TXT file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("")
            tmp.flush()

            result = self.extractor.extract_text_from_txt(Path(tmp.name))
            assert result == ""

        # Clean up
        Path(tmp.name).unlink()

    def test_extract_text_from_txt_file_not_found(self):
        """Test extraction from non-existent TXT file."""
        with pytest.raises(TextExtractionError, match="Text file not found"):
            self.extractor.extract_text_from_txt(Path("nonexistent.txt"))

    def test_extract_text_from_md_alias(self):
        """Test that extract_text_from_md is an alias for extract_text_from_txt."""
        test_content = "# Markdown Test\n\nThis is markdown content."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()

            result = self.extractor.extract_text_from_md(Path(tmp.name))
            assert result == test_content

        # Clean up
        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_success(self, mocker):
        """Test successful PDF text extraction."""
        # Mock PDF reader using pytest-mock
        mock_reader_instance = mocker.MagicMock()
        mock_reader_instance.is_encrypted = False
        mock_reader_instance.pages = [mocker.MagicMock(), mocker.MagicMock()]
        mock_reader_instance.pages[0].extract_text.return_value = "Page 1 content"
        mock_reader_instance.pages[1].extract_text.return_value = "Page 2 content"

        mock_pdf_reader = mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader")
        mock_pdf_reader.return_value = mock_reader_instance

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            result = self.extractor.extract_text_from_pdf(Path(tmp.name))
            assert result == "Page 1 content\n\nPage 2 content"

        # Clean up
        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_encrypted(self, mocker):
        """Test PDF extraction from encrypted file."""
        mock_reader_instance = mocker.MagicMock()
        mock_reader_instance.is_encrypted = True

        mock_pdf_reader = mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader")
        mock_pdf_reader.return_value = mock_reader_instance

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="PDF file is encrypted"):
                self.extractor.extract_text_from_pdf(Path(tmp.name))

        # Clean up
        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_no_pages(self, mocker):
        """Test PDF extraction from file with no pages."""
        mock_reader_instance = mocker.MagicMock()
        mock_reader_instance.pages = []  # No pages
        mock_reader_instance.is_encrypted = False

        mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader", return_value=mock_reader_instance)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            result = self.extractor.extract_text_from_pdf(Path(tmp.name))
            assert result == ""

        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_permission_error(self, mocker):
        """Test PDF extraction with permission error."""
        # Mock the file open operation to raise PermissionError
        mocker.patch("builtins.open", side_effect=PermissionError("Access denied"))

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="Permission denied"):
                self.extractor.extract_text_from_pdf(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_file_not_found(self):
        """Test PDF extraction from non-existent file."""
        with pytest.raises(TextExtractionError, match="PDF file not found"):
            self.extractor.extract_text_from_pdf(Path("nonexistent.pdf"))

    def test_extract_text_from_docx_success(self, mocker):
        """Test successful DOCX text extraction."""
        # Mock document using pytest-mock
        mock_doc = mocker.MagicMock()
        mock_paragraph1 = mocker.MagicMock()
        mock_paragraph1.text = "First paragraph"
        mock_paragraph2 = mocker.MagicMock()
        mock_paragraph2.text = "Second paragraph"
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
        mock_doc.tables = []

        mock_document = mocker.patch("src.document_to_anki.utils.text_extractor.Document")
        mock_document.return_value = mock_doc

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            result = self.extractor.extract_text_from_docx(Path(tmp.name))
            assert result == "First paragraph\n\nSecond paragraph"

        # Clean up
        Path(tmp.name).unlink()

    def test_extract_text_from_docx_file_not_found(self):
        """Test DOCX extraction from non-existent file."""
        with pytest.raises(TextExtractionError, match="Unexpected error extracting from DOCX"):
            self.extractor.extract_text_from_docx(Path("nonexistent.docx"))

    def test_extract_text_from_docx_permission_error(self, mocker):
        """Test DOCX extraction with permission error."""
        mocker.patch("src.document_to_anki.utils.text_extractor.Document", side_effect=PermissionError("Access denied"))

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="Permission denied"):
                self.extractor.extract_text_from_docx(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_docx_corrupted_file(self, mocker):
        """Test DOCX extraction from corrupted file."""
        mocker.patch("src.document_to_anki.utils.text_extractor.Document", side_effect=Exception("not a zip file"))

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="Invalid or corrupted DOCX file"):
                self.extractor.extract_text_from_docx(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_docx_empty_content(self, mocker):
        """Test DOCX extraction from file with no text content."""
        mock_doc = mocker.MagicMock()
        mock_doc.paragraphs = []
        mock_doc.tables = []

        mocker.patch("src.document_to_anki.utils.text_extractor.Document", return_value=mock_doc)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            result = self.extractor.extract_text_from_docx(Path(tmp.name))
            assert result == ""

        Path(tmp.name).unlink()

    def test_extract_text_integration_txt(self):
        """Test integration of extract_text method with TXT file."""
        test_content = "Integration test content"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()

            result = self.extractor.extract_text(Path(tmp.name))
            assert result == test_content

        # Clean up
        Path(tmp.name).unlink()

    def test_extract_text_exception_handling(self, mocker):
        """Test exception handling in extract_text method."""
        # Mock extract_text_from_txt to raise a non-TextExtractionError
        mocker.patch.object(self.extractor, "extract_text_from_txt", side_effect=ValueError("Unexpected error"))

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"test content")
            tmp.flush()

            with pytest.raises(TextExtractionError, match="Failed to extract text"):
                self.extractor.extract_text(Path(tmp.name))

            Path(tmp.name).unlink()

    def test_extract_text_path_not_file(self, tmp_path):
        """Test extraction when path is not a file."""
        # Create a directory instead of a file
        dir_path = tmp_path / "test_dir"
        dir_path.mkdir()

        with pytest.raises(TextExtractionError, match="Path is not a file"):
            self.extractor.extract_text(dir_path)

    def test_extract_text_from_pdf_reader_initialization_error(self, mocker):
        """Test PDF extraction when PdfReader initialization fails completely."""
        # Mock PdfReader to raise an exception on initialization
        mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader", side_effect=Exception("PDF reader failed"))
        # Mock HAS_PDFPLUMBER to False to test the error path
        mocker.patch("src.document_to_anki.utils.text_extractor.HAS_PDFPLUMBER", False)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="Could not initialize PDF reader"):
                self.extractor.extract_text_from_pdf(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_with_pdfplumber_fallback(self, mocker):
        """Test PDF extraction falling back to pdfplumber when PyPDF2 fails."""
        # Mock PyPDF2 to fail
        mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader", side_effect=Exception("PyPDF2 failed"))
        # Mock HAS_PDFPLUMBER to True
        mocker.patch("src.document_to_anki.utils.text_extractor.HAS_PDFPLUMBER", True)
        # Mock the pdfplumber fallback method
        mock_fallback = mocker.patch.object(self.extractor, "_extract_with_pdfplumber", return_value="Fallback text")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            result = self.extractor.extract_text_from_pdf(Path(tmp.name))
            assert result == "Fallback text"
            mock_fallback.assert_called_once_with(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_malformed_pages(self, mocker):
        """Test PDF extraction with some malformed pages."""
        mock_reader_instance = mocker.MagicMock()
        mock_reader_instance.is_encrypted = False
        
        # Create pages with mixed success/failure
        mock_page1 = mocker.MagicMock()
        mock_page1.extract_text.return_value = "Good page content"
        
        mock_page2 = mocker.MagicMock()
        mock_page2.extract_text.side_effect = AttributeError("NullObject error")
        
        mock_page3 = mocker.MagicMock()
        mock_page3.extract_text.return_value = "Another good page"
        
        mock_reader_instance.pages = [mock_page1, mock_page2, mock_page3]

        mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader", return_value=mock_reader_instance)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            result = self.extractor.extract_text_from_pdf(Path(tmp.name))
            assert result == "Good page content\n\nAnother good page"

        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_no_text_content(self, mocker):
        """Test PDF extraction when no text content is found."""
        mock_reader_instance = mocker.MagicMock()
        mock_reader_instance.is_encrypted = False
        
        # Create pages with empty or whitespace-only content
        mock_page1 = mocker.MagicMock()
        mock_page1.extract_text.return_value = "   "  # Only whitespace
        
        mock_page2 = mocker.MagicMock()
        mock_page2.extract_text.return_value = ""  # Empty
        
        mock_reader_instance.pages = [mock_page1, mock_page2]

        mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader", return_value=mock_reader_instance)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="No text content could be extracted from PDF"):
                self.extractor.extract_text_from_pdf(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_pdf_corrupted_pdf_error(self, mocker):
        """Test PDF extraction with PDF-specific errors."""
        # Mock to raise a PDF-specific error
        pdf_error = Exception("PdfReadError: Invalid PDF")
        mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader", side_effect=pdf_error)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="Invalid or corrupted PDF file"):
                self.extractor.extract_text_from_pdf(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_with_pdfplumber_success(self, mocker):
        """Test successful pdfplumber extraction."""
        # Mock pdfplumber
        mock_pdf = mocker.MagicMock()
        mock_page1 = mocker.MagicMock()
        mock_page1.extract_text.return_value = "Page 1 from pdfplumber"
        mock_page2 = mocker.MagicMock()
        mock_page2.extract_text.return_value = "Page 2 from pdfplumber"
        mock_pdf.pages = [mock_page1, mock_page2]
        
        mock_pdfplumber = mocker.MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mocker.patch("src.document_to_anki.utils.text_extractor.pdfplumber", mock_pdfplumber)
        mocker.patch("src.document_to_anki.utils.text_extractor.HAS_PDFPLUMBER", True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            result = self.extractor._extract_with_pdfplumber(Path(tmp.name))
            assert result == "Page 1 from pdfplumber\n\nPage 2 from pdfplumber"

        Path(tmp.name).unlink()

    def test_extract_with_pdfplumber_not_available(self, mocker):
        """Test pdfplumber extraction when pdfplumber is not available."""
        # Mock HAS_PDFPLUMBER to False to simulate pdfplumber not being available
        mocker.patch("src.document_to_anki.utils.text_extractor.HAS_PDFPLUMBER", False)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="pdfplumber is not available"):
                self.extractor._extract_with_pdfplumber(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_docx_with_tables(self, mocker):
        """Test DOCX extraction including table content."""
        # Mock document with paragraphs and tables
        mock_doc = mocker.MagicMock()
        
        # Mock paragraphs
        mock_paragraph = mocker.MagicMock()
        mock_paragraph.text = "Document paragraph"
        mock_doc.paragraphs = [mock_paragraph]
        
        # Mock tables
        mock_cell1 = mocker.MagicMock()
        mock_cell1.text = "Cell 1"
        mock_cell2 = mocker.MagicMock()
        mock_cell2.text = "Cell 2"
        mock_cell3 = mocker.MagicMock()
        mock_cell3.text = "  "  # Empty cell (whitespace only)
        
        mock_row1 = mocker.MagicMock()
        mock_row1.cells = [mock_cell1, mock_cell2]
        mock_row2 = mocker.MagicMock()
        mock_row2.cells = [mock_cell3]  # Row with only empty cells
        
        mock_table = mocker.MagicMock()
        mock_table.rows = [mock_row1, mock_row2]
        mock_doc.tables = [mock_table]

        mocker.patch("src.document_to_anki.utils.text_extractor.Document", return_value=mock_doc)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            result = self.extractor.extract_text_from_docx(Path(tmp.name))
            assert result == "Document paragraph\n\nCell 1 | Cell 2"

        Path(tmp.name).unlink()

    def test_extract_text_from_txt_encoding_fallback(self, mocker):
        """Test text extraction with encoding fallback."""
        # Create a file with latin-1 encoding
        test_content = "Café résumé naïve"  # Contains non-ASCII characters
        
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
            # Write content in latin-1 encoding
            tmp.write(test_content.encode('latin-1'))
            tmp.flush()

            # Mock the first encoding (utf-8) to fail
            original_open = open
            def mock_open(*args, **kwargs):
                if 'encoding' in kwargs and kwargs['encoding'] == 'utf-8':
                    raise UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
                return original_open(*args, **kwargs)
            
            mocker.patch("builtins.open", side_effect=mock_open)

            result = self.extractor.extract_text_from_txt(Path(tmp.name))
            # The result should be the content (may have encoding differences)
            assert len(result) > 0

        Path(tmp.name).unlink()

    def test_extract_text_from_txt_all_encodings_fail(self, mocker):
        """Test text extraction when all encodings fail."""
        # Mock open to always raise UnicodeDecodeError
        mocker.patch("builtins.open", side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte'))

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="Could not decode text file with any supported encoding"):
                self.extractor.extract_text_from_txt(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_txt_permission_error(self, mocker):
        """Test text extraction with permission error."""
        mocker.patch("builtins.open", side_effect=PermissionError("Access denied"))

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="Permission denied accessing text file"):
                self.extractor.extract_text_from_txt(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_integration_pdf(self, mocker):
        """Test integration of extract_text method with PDF file."""
        # Mock PDF extraction
        mock_reader_instance = mocker.MagicMock()
        mock_reader_instance.is_encrypted = False
        mock_reader_instance.pages = [mocker.MagicMock()]
        mock_reader_instance.pages[0].extract_text.return_value = "PDF integration test"

        mocker.patch("src.document_to_anki.utils.text_extractor.PdfReader", return_value=mock_reader_instance)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            result = self.extractor.extract_text(Path(tmp.name))
            assert result == "PDF integration test"

        Path(tmp.name).unlink()

    def test_extract_text_integration_docx(self, mocker):
        """Test integration of extract_text method with DOCX file."""
        # Mock DOCX extraction
        mock_doc = mocker.MagicMock()
        mock_paragraph = mocker.MagicMock()
        mock_paragraph.text = "DOCX integration test"
        mock_doc.paragraphs = [mock_paragraph]
        mock_doc.tables = []

        mocker.patch("src.document_to_anki.utils.text_extractor.Document", return_value=mock_doc)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            result = self.extractor.extract_text(Path(tmp.name))
            assert result == "DOCX integration test"

        Path(tmp.name).unlink()

    def test_extract_text_integration_md(self):
        """Test integration of extract_text method with MD file."""
        test_content = "# Markdown Integration Test\n\nThis is markdown content."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()

            result = self.extractor.extract_text(Path(tmp.name))
            assert result == test_content

        Path(tmp.name).unlink()

    def test_extract_with_pdfplumber_no_pages(self, mocker):
        """Test pdfplumber extraction with no pages."""
        mock_pdf = mocker.MagicMock()
        mock_pdf.pages = []  # No pages
        
        mock_pdfplumber = mocker.MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mocker.patch("src.document_to_anki.utils.text_extractor.pdfplumber", mock_pdfplumber)
        mocker.patch("src.document_to_anki.utils.text_extractor.HAS_PDFPLUMBER", True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            result = self.extractor._extract_with_pdfplumber(Path(tmp.name))
            assert result == ""

        Path(tmp.name).unlink()

    def test_extract_with_pdfplumber_no_text_content(self, mocker):
        """Test pdfplumber extraction when no text content is found."""
        mock_pdf = mocker.MagicMock()
        mock_page1 = mocker.MagicMock()
        mock_page1.extract_text.return_value = "   "  # Only whitespace
        mock_page2 = mocker.MagicMock()
        mock_page2.extract_text.return_value = ""  # Empty
        mock_pdf.pages = [mock_page1, mock_page2]
        
        mock_pdfplumber = mocker.MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mocker.patch("src.document_to_anki.utils.text_extractor.pdfplumber", mock_pdfplumber)
        mocker.patch("src.document_to_anki.utils.text_extractor.HAS_PDFPLUMBER", True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="No text content could be extracted from PDF using pdfplumber"):
                self.extractor._extract_with_pdfplumber(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_with_pdfplumber_partial_failure(self, mocker):
        """Test pdfplumber extraction with some page failures."""
        mock_pdf = mocker.MagicMock()
        mock_page1 = mocker.MagicMock()
        mock_page1.extract_text.return_value = "Good page"
        mock_page2 = mocker.MagicMock()
        mock_page2.extract_text.side_effect = Exception("Page extraction failed")
        mock_page3 = mocker.MagicMock()
        mock_page3.extract_text.return_value = "Another good page"
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        
        mock_pdfplumber = mocker.MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mocker.patch("src.document_to_anki.utils.text_extractor.pdfplumber", mock_pdfplumber)
        mocker.patch("src.document_to_anki.utils.text_extractor.HAS_PDFPLUMBER", True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            result = self.extractor._extract_with_pdfplumber(Path(tmp.name))
            assert result == "Good page\n\nAnother good page"

        Path(tmp.name).unlink()

    def test_extract_with_pdfplumber_exception(self, mocker):
        """Test pdfplumber extraction with general exception."""
        mock_pdfplumber = mocker.MagicMock()
        mock_pdfplumber.open.side_effect = Exception("pdfplumber failed")
        mocker.patch("src.document_to_anki.utils.text_extractor.pdfplumber", mock_pdfplumber)
        mocker.patch("src.document_to_anki.utils.text_extractor.HAS_PDFPLUMBER", True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="pdfplumber extraction failed"):
                self.extractor._extract_with_pdfplumber(Path(tmp.name))

        Path(tmp.name).unlink()

    def test_extract_text_from_docx_file_not_found_specific(self, mocker):
        """Test DOCX extraction with specific file not found error."""
        mocker.patch("src.document_to_anki.utils.text_extractor.Document", side_effect=Exception("no such file"))

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            with pytest.raises(TextExtractionError, match="DOCX file not found"):
                self.extractor.extract_text_from_docx(Path(tmp.name))

        Path(tmp.name).unlink()
