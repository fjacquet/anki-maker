"""
Document to Anki CLI - Convert documents to Anki flashcards using LLM.

A comprehensive tool that transforms various document formats (PDF, DOCX, TXT, MD)
into high-quality Anki flashcards using Google's Gemini Pro AI model. The application
provides both CLI and web interfaces for flexible usage.

Key Features:
- Multi-format document processing (PDF, DOCX, TXT, MD, ZIP)
- AI-powered flashcard generation using Gemini Pro
- Interactive flashcard management (preview, edit, delete, add)
- Both command-line and web interfaces
- Batch processing capabilities
- Rich progress tracking and error handling
- Anki-compatible CSV export
- Session-based web interface with real-time updates
- Comprehensive logging and diagnostics

Modules:
    cli: Command-line interface implementation
    web: FastAPI web application and REST API
    core: Core business logic (document processing, flashcard generation, LLM client)
    models: Pydantic data models for flashcards and processing results
    utils: Utility modules for file handling and text extraction

Usage Examples:
    # CLI usage
    from document_to_anki.cli.main import main

    # Python API usage
    from document_to_anki.core.document_processor import DocumentProcessor
    from document_to_anki.core.flashcard_generator import FlashcardGenerator

    processor = DocumentProcessor()
    generator = FlashcardGenerator()

    # Process document and generate flashcards
    result = processor.process_upload("document.pdf")
    flashcards = generator.generate_flashcards([result.text_content])

Requirements:
    - Python 3.12+
    - Google Gemini API key
    - Internet connection for AI processing

Installation:
    pip install -e .
    # or
    uv sync

Configuration:
    Set GEMINI_API_KEY environment variable or create .env file
"""

__version__ = "0.1.0"
__author__ = "Document to Anki CLI Team"
__email__ = "support@document-to-anki.com"
__license__ = "MIT"

# Public API exports
from .config import ConfigurationError, ModelConfig
from .core.document_processor import DocumentProcessingError, DocumentProcessor
from .core.flashcard_generator import FlashcardGenerationError, FlashcardGenerator
from .core.llm_client import LLMClient
from .models.flashcard import Flashcard, ProcessingResult

__all__ = [
    "ModelConfig",
    "ConfigurationError",
    "DocumentProcessor",
    "DocumentProcessingError",
    "FlashcardGenerator",
    "FlashcardGenerationError",
    "LLMClient",
    "Flashcard",
    "ProcessingResult",
]
