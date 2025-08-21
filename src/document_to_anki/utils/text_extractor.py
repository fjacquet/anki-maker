"""Text extraction utilities for various document formats."""

from pathlib import Path

import pypdf
from docx import Document
from loguru import logger


class TextExtractionError(Exception):
    """Exception raised when text extraction fails."""

    pass


class TextExtractor:
    """Handles text extraction from various document formats."""

    SUPPORTED_FORMATS = {".pdf", ".docx", ".txt", ".md"}

    def __init__(self):
        """Initialize the TextExtractor."""
        self.logger = logger

    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from a file based on its extension.

        Args:
            file_path: Path to the file to extract text from

        Returns:
            Extracted text content as a string

        Raises:
            TextExtractionError: If extraction fails or format is unsupported
        """
        if not file_path.exists():
            raise TextExtractionError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise TextExtractionError(f"Path is not a file: {file_path}")

        file_extension = file_path.suffix.lower()

        if file_extension not in self.SUPPORTED_FORMATS:
            raise TextExtractionError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        try:
            if file_extension == ".pdf":
                return self.extract_text_from_pdf(file_path)
            elif file_extension == ".docx":
                return self.extract_text_from_docx(file_path)
            elif file_extension in {".txt", ".md"}:
                return self.extract_text_from_txt(file_path)
            else:
                raise TextExtractionError(f"Unsupported file format: {file_extension}")

        except Exception as e:
            if isinstance(e, TextExtractionError):
                raise
            raise TextExtractionError(f"Failed to extract text from {file_path}: {str(e)}") from e

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from a PDF file using PyPDF2.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content as a string

        Raises:
            TextExtractionError: If PDF extraction fails
        """
        try:
            text_content = []

            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)

                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    raise TextExtractionError(f"PDF file is encrypted: {file_path}")

                # Check if PDF has pages
                if len(pdf_reader.pages) == 0:
                    self.logger.warning(f"PDF file has no pages: {file_path}")
                    return ""

                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():  # Only add non-empty pages
                            text_content.append(page_text)
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to extract text from page {page_num + 1} in {file_path}: {e}"
                        )
                        continue

                extracted_text = "\n\n".join(text_content)

                if not extracted_text.strip():
                    self.logger.warning(f"No text content extracted from PDF: {file_path}")
                    return ""

                self.logger.info(
                    f"Successfully extracted text from PDF: {file_path} ({len(pdf_reader.pages)} pages)"
                )
                return extracted_text

        except FileNotFoundError as e:
            raise TextExtractionError(f"PDF file not found: {file_path}") from e
        except PermissionError as e:
            raise TextExtractionError(f"Permission denied accessing PDF file: {file_path}") from e
        except pypdf.errors.PdfReadError as e:
            raise TextExtractionError(f"Invalid or corrupted PDF file: {file_path} - {str(e)}") from e
        except Exception as e:
            raise TextExtractionError(f"Unexpected error extracting from PDF {file_path}: {str(e)}") from e

    def extract_text_from_docx(self, file_path: Path) -> str:
        """
        Extract text from a DOCX file using python-docx.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Extracted text content as a string

        Raises:
            TextExtractionError: If DOCX extraction fails
        """
        try:
            doc = Document(file_path)
            text_content = []

            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():  # Only add non-empty paragraphs
                    text_content.append(paragraph.text)

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content.append(" | ".join(row_text))

            extracted_text = "\n\n".join(text_content)

            if not extracted_text.strip():
                self.logger.warning(f"No text content extracted from DOCX: {file_path}")
                return ""

            self.logger.info(f"Successfully extracted text from DOCX: {file_path}")
            return extracted_text

        except FileNotFoundError as e:
            raise TextExtractionError(f"DOCX file not found: {file_path}") from e
        except PermissionError as e:
            raise TextExtractionError(f"Permission denied accessing DOCX file: {file_path}") from e
        except Exception as e:
            # Handle various docx-related errors
            error_msg = str(e).lower()
            if "not a zip file" in error_msg or "bad zipfile" in error_msg:
                raise TextExtractionError(f"Invalid or corrupted DOCX file: {file_path}") from e
            elif "no such file" in error_msg:
                raise TextExtractionError(f"DOCX file not found: {file_path}") from e
            else:
                raise TextExtractionError(
                    f"Unexpected error extracting from DOCX {file_path}: {str(e)}"
                ) from e

    def extract_text_from_txt(self, file_path: Path) -> str:
        """
        Extract text from a TXT or MD file.

        Args:
            file_path: Path to the text file

        Returns:
            Extracted text content as a string

        Raises:
            TextExtractionError: If text extraction fails
        """
        try:
            # Try different encodings in order of preference
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

            for encoding in encodings:
                try:
                    with open(file_path, encoding=encoding) as file:
                        content = file.read()

                    if not content.strip():
                        self.logger.warning(f"Text file is empty: {file_path}")
                        return ""

                    self.logger.info(
                        f"Successfully extracted text from {file_path.suffix.upper()} file: {file_path} "
                        f"(encoding: {encoding})"
                    )
                    return content

                except UnicodeDecodeError:
                    continue  # Try next encoding

            # If all encodings failed
            raise TextExtractionError(f"Could not decode text file with any supported encoding: {file_path}")

        except FileNotFoundError as e:
            raise TextExtractionError(f"Text file not found: {file_path}") from e
        except PermissionError as e:
            raise TextExtractionError(f"Permission denied accessing text file: {file_path}") from e
        except Exception as e:
            raise TextExtractionError(
                f"Unexpected error extracting from text file {file_path}: {str(e)}"
            ) from e

    def extract_text_from_md(self, file_path: Path) -> str:
        """
        Extract text from a Markdown file.

        This is an alias for extract_text_from_txt since both are plain text files.

        Args:
            file_path: Path to the markdown file

        Returns:
            Extracted text content as a string

        Raises:
            TextExtractionError: If text extraction fails
        """
        return self.extract_text_from_txt(file_path)

    def is_supported_format(self, file_path: Path) -> bool:
        """
        Check if a file format is supported for text extraction.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file format is supported, False otherwise
        """
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS

    def get_supported_formats(self) -> set[str]:
        """
        Get the set of supported file formats.

        Returns:
            Set of supported file extensions (including the dot)
        """
        return self.SUPPORTED_FORMATS.copy()
