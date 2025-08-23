# Design Document

## Overview

The Document-to-Anki CLI application is a modern Python tool that converts various document formats into Anki flashcards using the Gemini LLM. The system provides both CLI and web interfaces, allowing users to upload documents, preview/edit generated flashcards, and export them as Anki-compatible CSV files.

The application follows modern Python development practices using Python 3.12+, uv for package management, and incorporates best-in-class tools for development, testing, and user experience.

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
document-to-anki-cli/
├── src/
│   ├── document_to_anki/
│   │   ├── __init__.py
│   │   ├── cli/
│   │   │   ├── __init__.py
│   │   │   └── main.py           # CLI entry point
│   │   ├── web/
│   │   │   ├── __init__.py
│   │   │   ├── app.py            # FastAPI web application
│   │   │   └── static/           # Web assets
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── flashcard_generator.py
│   │   │   └── llm_client.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── flashcard.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_handler.py
│   │       └── text_extractor.py
├── tests/
├── pyproject.toml
└── README.md
```

### Key Architectural Principles

1. **Separation of Concerns**: CLI, web, and core logic are separated into distinct modules
2. **Dependency Injection**: Core services are injected to enable testing and flexibility
3. **Single Responsibility**: Each module has a clear, focused purpose
4. **Testability**: All components are designed to be easily testable with mocking

## Components and Interfaces

### Configuration Management

The application supports configurable LLM models through environment variables, providing flexibility in model selection and cost optimization.

#### Model Configuration Strategy

```python
class ModelConfig:
    """Handles LLM model configuration and validation."""
    
    SUPPORTED_MODELS = {
        "gemini/gemini-2.5-flash": "GEMINI_API_KEY",
        "gemini/gemini-2.5-pro": "GEMINI_API_KEY",
        "openai/gpt-4": "OPENAI_API_KEY", 
        "openai/gpt-3.5-turbo": "OPENAI_API_KEY",
        "openai/gpt-4.1": "OPENAI_API_KEY",
        "openai/gpt-4.1-mini": "OPENAI_API_KEY",
        "openai/gpt-4.1-nano": "OPENAI_API_KEY",
        "openai/gpt-5": "OPENAI_API_KEY",
        "openai/gpt-5-mini": "OPENAI_API_KEY",
        "openai/gpt-5-nano": "OPENAI_API_KEY",
        "openai/gpt-4o": "OPENAI_API_KEY"
    }
    
    DEFAULT_MODEL = "gemini/gemini-2.5-flash"
    
    @classmethod
    def get_model_from_env(cls) -> str:
        """Get model from MODEL environment variable or return default."""
        return os.getenv("MODEL", cls.DEFAULT_MODEL)
    
    @classmethod
    def validate_model_config(cls, model: str) -> bool:
        """Validate that model is supported and API key is available."""
        if model not in cls.SUPPORTED_MODELS:
            return False
        
        required_key = cls.SUPPORTED_MODELS[model]
        return os.getenv(required_key) is not None
    
    @classmethod
    def get_supported_models(cls) -> List[str]:
        """Return list of supported model identifiers."""
        return list(cls.SUPPORTED_MODELS.keys())
```

**Design Rationale**: This approach provides clear separation between configuration logic and business logic, making it easy to add new models and maintain API key requirements. The environment variable approach follows twelve-factor app principles for configuration management.

### Core Components

#### DocumentProcessor
Handles document upload, validation, and text extraction.

```python
class DocumentProcessor:
    def process_upload(self, file_path: Path) -> List[str]
    def extract_text_from_file(self, file_path: Path) -> str
    def process_zip_archive(self, zip_path: Path) -> List[str]
    def process_folder(self, folder_path: Path) -> List[str]
```

#### FlashcardGenerator
Manages flashcard creation, editing, and export functionality.

```python
class FlashcardGenerator:
    def generate_flashcards(self, text_content: List[str]) -> List[Flashcard]
    def preview_flashcards(self, flashcards: List[Flashcard]) -> None
    def edit_flashcard(self, flashcard_id: str, question: str, answer: str) -> None
    def delete_flashcard(self, flashcard_id: str) -> None
    def add_flashcard(self, question: str, answer: str, card_type: str) -> None
    def export_to_csv(self, flashcards: List[Flashcard], output_path: Path) -> None
```

#### LLMClient
Handles communication with configurable LLM models through litellm, supporting multiple providers.

```python
class LLMClient:
    def __init__(self, model: str = None)
    def generate_flashcards_from_text(self, text: str) -> List[Dict[str, str]]
    def chunk_text_for_processing(self, text: str, max_tokens: int) -> List[str]
    def validate_model_and_api_key(self, model: str) -> bool
    def get_supported_models(self) -> List[str]
```

### Web Interface Components

#### FastAPI Application
- File upload endpoints with drag-and-drop support
- Progress tracking for long-running operations
- Flashcard preview and editing interface
- CSV export functionality
- Model configuration status endpoint
- Environment variable validation for API keys

#### Frontend (HTML/CSS/JavaScript)
- Responsive design using modern CSS Grid/Flexbox
- Accessible components following WCAG 2.1 AA standards
- Progress indicators and real-time feedback
- Interactive flashcard editing interface

### CLI Interface

#### Click-based CLI
- Command-line argument parsing with model configuration options
- Environment variable support for MODEL selection
- Rich-enhanced output with progress bars
- Batch processing capabilities
- Verbose logging options
- Model validation and helpful error messages for configuration issues

## Data Models

### Flashcard Model

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional

class Flashcard(BaseModel):
    """Represents a single flashcard with question, answer, and metadata."""
    
    id: str
    question: str
    answer: str
    card_type: Literal["qa", "cloze"]  # "qa" for question-answer, "cloze" for cloze deletion
    source_file: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator("question", "answer")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Validate that question and answer are not empty."""
        if not v or not v.strip():
            raise ValueError("Question and answer cannot be empty")
        return v.strip()
    
    @model_validator(mode="after")
    def validate_cloze_format(self) -> "Flashcard":
        """Validate cloze deletion format for cloze cards."""
        if self.card_type == "cloze":
            if "{{c1::" not in self.question and "{{c1::" not in self.answer:
                raise ValueError("Cloze cards must contain cloze deletion format {{c1::...}}")
        return self
    
    def to_csv_row(self) -> List[str]:
        """Convert flashcard to Anki-compatible CSV format"""
        return [self.question.strip(), self.answer.strip(), self.card_type, self.source_file or ""]
    
    def validate(self) -> bool:
        """Validate flashcard content"""
        try:
            # Pydantic validation happens automatically, so if we get here, it's valid
            return True
        except Exception:
            return False
```

### Processing Result Model

```python
class ProcessingResult(BaseModel):
    """Represents the result of document processing operation."""
    
    flashcards: List[Flashcard]
    source_files: List[str]
    processing_time: float
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Check if processing was successful (no errors)."""
        return len(self.errors) == 0
    
    @property
    def flashcard_count(self) -> int:
        """Get the total number of flashcards generated."""
        return len(self.flashcards)
```

## Error Handling

### Error Categories

1. **File Processing Errors**
   - Unsupported file formats
   - Corrupted files
   - Permission issues
   - File size limitations

2. **LLM Integration Errors**
   - API rate limiting
   - Network connectivity issues
   - Invalid API responses
   - Token limit exceeded

3. **Configuration Errors**
   - Invalid model specification
   - Missing API keys for selected model
   - Unsupported model providers

4. **Data Validation Errors**
   - Invalid flashcard content
   - Missing required fields
   - Export format issues

### Error Handling Strategy

```python
class DocumentToAnkiError(Exception):
    """Base exception for the application"""
    pass

class FileProcessingError(DocumentToAnkiError):
    """Errors related to file processing"""
    pass

class LLMError(DocumentToAnkiError):
    """Errors related to LLM communication"""
    pass

class ConfigurationError(DocumentToAnkiError):
    """Errors related to model configuration and API keys"""
    pass

class ValidationError(DocumentToAnkiError):
    """Errors related to data validation"""
    pass
```

### Error Recovery

- Retry mechanisms for transient LLM API errors
- Graceful degradation when processing individual files fails
- Clear error messages with suggested solutions for configuration issues
- Automatic fallback to default model when invalid model is specified
- Comprehensive logging for debugging including model configuration details

## Testing Strategy

### Test Structure

```
tests/
├── unit/
│   ├── test_document_processor.py
│   ├── test_flashcard_generator.py
│   ├── test_llm_client.py
│   └── test_models.py
├── integration/
│   ├── test_cli_integration.py
│   ├── test_web_integration.py
│   └── test_end_to_end.py
├── fixtures/
│   ├── sample_documents/
│   └── expected_outputs/
└── conftest.py
```

### Testing Approach

1. **Unit Tests**: Test individual components in isolation using pytest-mock (avoiding unittest.mock)
2. **Integration Tests**: Test component interactions and API endpoints
3. **End-to-End Tests**: Test complete workflows from document upload to CSV export
4. **Performance Tests**: Validate processing speed and memory usage with large documents

### Test Coverage Goals

- Minimum 80% code coverage
- 100% coverage for critical paths (LLM integration, file processing)
- Mock external dependencies using pytest-mock's mocker fixture (LLM API, file system operations)
- Test error conditions and edge cases

### Quality Assurance

- **Linting**: ruff for code formatting and style enforcement
- **Type Checking**: mypy for static type analysis
- **Security**: bandit for security vulnerability scanning
- **Dependencies**: safety for dependency vulnerability checking

## Technology Stack

### Core Dependencies

- **Python 3.12+**: Modern Python features and performance improvements
- **uv**: Fast package management and dependency resolution
- **Pydantic v2**: Modern data validation and serialization with type safety
- **litellm**: Unified LLM API interface supporting multiple providers (Gemini, OpenAI, etc.)
- **pandas**: Efficient data manipulation for CSV processing
- **numpy**: Numerical operations for text processing

### CLI Dependencies

- **click**: Command-line interface framework
- **rich**: Enhanced terminal output and progress indicators
- **loguru**: Structured logging with rich formatting

### Web Dependencies

- **FastAPI**: Modern, fast web framework
- **uvicorn**: ASGI server for FastAPI
- **Jinja2**: Template engine for HTML rendering
- **python-multipart**: File upload handling

### Development Dependencies

- **pytest**: Testing framework
- **pytest-mock**: Mocking utilities for tests
- **pytest-cov**: Code coverage reporting
- **ruff**: Linting and formatting
- **mypy**: Static type checking

### Document Processing

- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX document processing
- **zipfile**: Built-in ZIP archive handling
- **pathlib**: Modern path handling

## Performance Considerations

### Text Processing Optimization

- Chunking large documents to stay within LLM token limits
- Streaming processing for memory efficiency
- Parallel processing for multiple files
- Caching of processed content to avoid reprocessing

### LLM Integration Optimization

- Configurable model selection via environment variables for cost and performance optimization
- Support for multiple LLM providers (Gemini, OpenAI, etc.) with provider-specific optimizations
- Automatic API key validation based on selected model to fail fast on configuration errors
- Model-specific token limit handling (different limits for different providers)
- Batch processing of text chunks optimized per model capabilities
- Retry logic with exponential backoff
- Rate limiting to respect API constraints per provider
- Response caching for identical content

### Web Interface Performance

- Asynchronous file processing
- Progress tracking for long-running operations
- Client-side validation to reduce server load
- Efficient file upload handling

## Security Considerations

### File Upload Security

- File type validation and sanitization
- File size limits to prevent DoS attacks
- Temporary file cleanup
- Path traversal protection

### API Security

- Input validation and sanitization
- Rate limiting for API endpoints
- Secure handling of multiple API keys (GEMINI_API_KEY, OPENAI_API_KEY)
- Environment variable validation for model configuration
- CORS configuration for web interface

### Data Privacy

- No persistent storage of user documents
- Secure handling of temporary files
- Clear data retention policies
- Optional local-only processing mode