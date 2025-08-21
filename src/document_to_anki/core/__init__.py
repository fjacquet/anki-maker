"""Core functionality for document processing and flashcard generation."""

from .document_processor import DocumentProcessor, DocumentProcessingError, DocumentProcessingResult

__all__ = ["DocumentProcessor", "DocumentProcessingError", "DocumentProcessingResult"]
