"""PDF text extraction utilities."""

from pathlib import Path

from loguru import logger
from pypdf import PdfReader

from .text_extractor_common import TextExtractionError

try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_PDFPLUMBER = False


def extract_text(file_path: Path) -> str:
    """Extract text from a PDF file using pypdf.

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
            try:
                pdf_reader = PdfReader(file)
            except Exception as reader_error:
                file.seek(0)
                try:
                    pdf_reader = PdfReader(file)
                except Exception as fallback_error:
                    if HAS_PDFPLUMBER:
                        logger.warning(
                            f"PyPDF failed for {file_path}, trying pdfplumber..."
                        )
                        return _extract_with_pdfplumber(file_path)
                    raise TextExtractionError(
                        f"Could not initialize PDF reader for {file_path}. "
                        f"The PDF may be severely corrupted or use an unsupported format. "
                        f"Original error: {reader_error}, Fallback error: {fallback_error}"
                    ) from fallback_error

            if pdf_reader.is_encrypted:
                raise TextExtractionError(f"PDF file is encrypted: {file_path}")
            if len(pdf_reader.pages) == 0:
                logger.warning(f"PDF file has no pages: {file_path}")
                return ""

            successful_pages = 0
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(page_text)
                        successful_pages += 1
                except (AttributeError, TypeError) as e:
                    logger.warning(
                        f"Skipping malformed page {page_num + 1} in {file_path}: {e}"
                    )
                    continue
                except Exception as e:  # pragma: no cover - defensive
                    logger.warning(
                        f"Failed to extract text from page {page_num + 1} in {file_path}: {e}"
                    )
                    continue

            extracted_text = "\n\n".join(text_content)
            if not extracted_text.strip():
                if successful_pages == 0:
                    raise TextExtractionError(
                        f"No text content could be extracted from PDF: {file_path}. "
                        f"The PDF may be image-based, corrupted, or use unsupported formatting."
                    )
                logger.warning(f"No text content extracted from PDF: {file_path}")
                return ""

            logger.info(
                f"Successfully extracted text from PDF: {file_path} "
                f"({successful_pages}/{len(pdf_reader.pages)} pages processed)"
            )
            return extracted_text
    except FileNotFoundError as e:
        raise TextExtractionError(f"PDF file not found: {file_path}") from e
    except PermissionError as e:
        raise TextExtractionError(
            f"Permission denied accessing PDF file: {file_path}"
        ) from e
    except Exception as e:
        error_msg = str(e)
        if "PdfReadError" in error_msg:
            raise TextExtractionError(
                f"Invalid or corrupted PDF file: {file_path} - {error_msg}"
            ) from e
        raise TextExtractionError(
            f"Unexpected error extracting from PDF {file_path}: {error_msg}"
        ) from e


def _extract_with_pdfplumber(file_path: Path) -> str:
    """Extract text using pdfplumber as a fallback method."""
    if not HAS_PDFPLUMBER:
        raise TextExtractionError("pdfplumber is not available")
    try:
        text_content = []
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                logger.warning(f"PDF file has no pages: {file_path}")
                return ""
            successful_pages = 0
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(page_text)
                        successful_pages += 1
                except Exception as e:  # pragma: no cover - defensive
                    logger.warning(
                        f"pdfplumber failed to extract text from page {page_num + 1} in {file_path}: {e}"
                    )
                    continue
            extracted_text = "\n\n".join(text_content)
            if not extracted_text.strip():
                if successful_pages == 0:
                    raise TextExtractionError(
                        f"No text content could be extracted from PDF using pdfplumber: {file_path}. "
                        f"The PDF may be image-based or use unsupported formatting."
                    )
                logger.warning(
                    f"No text content extracted from PDF using pdfplumber: {file_path}"
                )
                return ""
            logger.info(
                f"Successfully extracted text from PDF using pdfplumber: {file_path} "
                f"({successful_pages}/{len(pdf.pages)} pages processed)"
            )
            return extracted_text
    except Exception as e:
        raise TextExtractionError(
            f"pdfplumber extraction failed for {file_path}: {str(e)}"
        ) from e
