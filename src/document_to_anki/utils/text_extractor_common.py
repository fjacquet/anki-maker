"""Common utilities for text extraction."""

from pathlib import Path

from loguru import logger


class TextExtractionError(Exception):
    """Exception raised when text extraction fails."""

    pass


def extract_text(file_path: Path) -> str:
    """Extract text from a plain text or markdown file.

    Tries multiple encodings before giving up.

    Args:
        file_path: Path to the text file

    Returns:
        Extracted text content as a string

    Raises:
        TextExtractionError: If text extraction fails
    """
    try:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as file:
                    content = file.read()
                if not content.strip():
                    logger.warning(f"Text file is empty: {file_path}")
                    return ""
                logger.info(
                    f"Successfully extracted text from {file_path.suffix.upper()} file: {file_path} "
                    f"(encoding: {encoding})"
                )
                return content
            except UnicodeDecodeError:
                continue
        raise TextExtractionError(
            f"Could not decode text file with any supported encoding: {file_path}"
        )
    except FileNotFoundError as e:
        raise TextExtractionError(f"Text file not found: {file_path}") from e
    except PermissionError as e:
        raise TextExtractionError(
            f"Permission denied accessing text file: {file_path}"
        ) from e
    except Exception as e:
        raise TextExtractionError(
            f"Unexpected error extracting from text file {file_path}: {str(e)}"
        ) from e
