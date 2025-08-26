"""Text extraction utilities for various document formats."""

from pathlib import Path

from loguru import logger

from . import docx_extractor, pdf_extractor, pptx_extractor, text_extractor_common
from .text_extractor_common import TextExtractionError


class TextExtractor:
    """Handles text extraction from various document formats."""

    SUPPORTED_FORMATS = {".pdf", ".docx", ".pptx", ".txt", ".md"}
    _EXTRACTOR_MAP = {
        ".pdf": pdf_extractor.extract_text,
        ".docx": docx_extractor.extract_text,
        ".pptx": pptx_extractor.extract_text,
        ".txt": text_extractor_common.extract_text,
        ".md": text_extractor_common.extract_text,
    }

    def __init__(self) -> None:
        """Initialize the TextExtractor."""
        self.logger = logger

    def extract_text(self, file_path: Path) -> str:
        """Extract text from a file based on its extension."""
        if not file_path.exists():
            raise TextExtractionError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise TextExtractionError(f"Path is not a file: {file_path}")

        file_extension = file_path.suffix.lower()
        extractor = self._EXTRACTOR_MAP.get(file_extension)
        if extractor is None:
            raise TextExtractionError(
                f"Unsupported file format: {file_extension}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        try:
            return extractor(file_path)
        except Exception as e:
            if isinstance(e, TextExtractionError):
                raise
            raise TextExtractionError(f"Failed to extract text from {file_path}: {str(e)}") from e

    def is_supported_format(self, file_path: Path) -> bool:
        """Check if a file format is supported for text extraction."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS

    def get_supported_formats(self) -> set[str]:
        """Get the set of supported file formats."""
        return self.SUPPORTED_FORMATS.copy()


__all__ = ["TextExtractor", "TextExtractionError"]
