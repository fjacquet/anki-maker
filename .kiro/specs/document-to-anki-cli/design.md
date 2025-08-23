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
Manages flashcard creation, editing, and export functionality with French language validation and quality assurance.

```python
class FlashcardGenerator:
    def generate_flashcards(self, text_content: List[str], target_language: str = "french") -> List[Flashcard]
    def preview_flashcards(self, flashcards: List[Flashcard]) -> None
    def edit_flashcard(self, flashcard_id: str, question: str, answer: str) -> None
    def delete_flashcard(self, flashcard_id: str) -> None
    def add_flashcard(self, question: str, answer: str, card_type: str) -> None
    def export_to_csv(self, flashcards: List[Flashcard], output_path: Path) -> None
    def validate_language_quality(self, flashcards: List[Flashcard]) -> List[Flashcard]
    def regenerate_non_french_flashcards(self, flashcards: List[Flashcard]) -> List[Flashcard]
```

#### LLMClient
Handles communication with configurable LLM models through litellm, supporting multiple providers with French language output validation and regeneration capabilities.

```python
class LLMClient:
    def __init__(self, model: str = None)
    def generate_flashcards_from_text(self, text: str, language: str = "french") -> List[Dict[str, str]]
    def chunk_text_for_processing(self, text: str, max_tokens: int) -> List[str]
    def validate_model_and_api_key(self, model: str) -> bool
    def get_supported_models(self) -> List[str]
    def validate_french_output(self, flashcards: List[Dict[str, str]]) -> bool
    def regenerate_non_french_content(self, flashcard: Dict[str, str]) -> Dict[str, str]
    def get_french_prompt_template(self) -> str
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

5. **Language Processing Errors**
   - Non-French output from LLM
   - Grammar validation failures
   - Language detection issues
   - Repeated regeneration failures

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

class LanguageError(DocumentToAnkiError):
    """Errors related to French language processing and validation"""
    pass
```

### Error Recovery

- Retry mechanisms for transient LLM API errors
- Graceful degradation when processing individual files fails
- Clear error messages with suggested solutions for configuration issues
- Automatic fallback to default model when invalid model is specified
- Comprehensive logging for debugging including model configuration details
- Automatic regeneration of non-French content with enhanced prompts
- Language validation with clear feedback when French output cannot be achieved

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

## French Language Support

### Overview

The application is designed to generate flashcards exclusively in French, regardless of the source document language. This ensures consistent study materials for French-speaking users and provides an immersive learning experience.

### Language Processing Strategy

#### Prompt Engineering for French Output

The LLM integration includes carefully crafted prompts that explicitly instruct the model to generate French flashcards:

```python
FRENCH_FLASHCARD_PROMPT = """
Vous êtes un expert en création de cartes mémoire (flashcards) pour l'apprentissage.
Analysez le texte fourni et créez des cartes mémoire en français de haute qualité.

Instructions importantes:
1. Toutes les questions et réponses DOIVENT être en français
2. Utilisez une grammaire française correcte et un vocabulaire approprié
3. Créez des questions claires et concises avec des réponses précises
4. Générez un mélange de cartes question-réponse et de cartes à trous (cloze deletion)
5. Concentrez-vous sur les informations les plus importantes du texte
6. Adaptez le niveau de langue au contenu (académique, technique, général)

Format de sortie requis:
- Type: "qa" pour question-réponse, "cloze" pour suppression à trous
- Question: La question en français
- Réponse: La réponse en français

Texte à analyser:
{text}
"""
```

**Design Rationale**: This approach ensures that regardless of the input document language (English, Spanish, etc.), the output flashcards are always in French. The prompt includes specific instructions for French grammar, vocabulary usage, and appropriate language level adaptation.

#### Language Validation

The system implements validation to ensure French output quality:

```python
class FrenchLanguageValidator:
    """Validates that LLM output is in French and meets quality standards."""
    
    def validate_french_content(self, text: str) -> bool:
        """Validate that text is in French using linguistic patterns."""
        # Check for French linguistic markers
        french_indicators = [
            r'\b(le|la|les|un|une|des)\b',  # Articles
            r'\b(est|sont|était|étaient)\b',  # Common verbs
            r'\b(que|qui|dont|où)\b',  # Relative pronouns
            r'\b(avec|dans|pour|sur|sous)\b'  # Prepositions
        ]
        
        score = sum(1 for pattern in french_indicators 
                   if re.search(pattern, text.lower()))
        return score >= 2  # Minimum threshold for French detection
    
    def validate_flashcard_french(self, flashcard: Dict[str, str]) -> bool:
        """Validate that both question and answer are in French."""
        return (self.validate_french_content(flashcard['question']) and 
                self.validate_french_content(flashcard['answer']))
    
    def request_regeneration_if_needed(self, flashcards: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Request regeneration for non-French flashcards."""
        validated_flashcards = []
        for flashcard in flashcards:
            if not self.validate_flashcard_french(flashcard):
                # Log warning and request regeneration
                logger.warning(f"Non-French content detected, requesting regeneration")
                # Trigger regeneration with stronger French emphasis
                regenerated = self._regenerate_with_french_emphasis(flashcard)
                validated_flashcards.append(regenerated)
            else:
                validated_flashcards.append(flashcard)
        return validated_flashcards
```

#### Cloze Deletion in French

Special attention is given to French cloze deletion cards to ensure proper sentence structure:

```python
def create_french_cloze_cards(self, text: str) -> List[Dict[str, str]]:
    """Create cloze deletion cards with proper French syntax."""
    # French-specific cloze patterns that respect grammar rules
    # Example: "La {{c1::photosynthèse}} est le processus par lequel..."
    # Ensures grammatical agreement and natural French flow
```

**Design Rationale**: French has specific grammatical rules (gender agreement, verb conjugation, etc.) that must be considered when creating cloze deletion cards. The system accounts for these linguistic features to create natural-sounding French flashcards.

### Error Handling for Language Issues

The system includes specific error handling for language-related issues:

1. **Non-French Output Detection**: Automatic detection and regeneration of non-French content
2. **Grammar Validation**: Basic validation of French grammar patterns
3. **Fallback Mechanisms**: If repeated attempts fail to generate French content, the system provides clear error messages
4. **User Feedback**: Clear indication when language validation fails and regeneration is attempted

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
- French language output validation and regeneration for non-French responses

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
- Optional local-only processing mode## CI/CD Pipeline Alignment

### Overview

The CI/CD pipeline alignment ensures that GitHub Actions workflows use identical commands and logic as the project's Makefile, providing complete consistency between local development and CI environments. This eliminates discrepancies and ensures that developers can replicate CI behavior locally for debugging.

### Design Principles

#### Command Consistency
All CI workflow jobs must use the same Makefile targets that developers use locally:

- **Quality Checks**: `make quality` instead of individual ruff, mypy, bandit commands
- **Testing**: `make test`, `make ci-test`, or `make test-cov` instead of direct pytest calls
- **Dependency Installation**: `make install-dev` instead of `uv pip install -e ".[dev]"`
- **Build Process**: `make build` instead of direct `uv build`
- **Validation**: `make validate` instead of direct script calls

**Design Rationale**: This approach ensures that any changes to build logic, quality checks, or testing procedures only need to be made in the Makefile, and CI automatically inherits these changes without workflow modifications.

#### uv Command Consistency
All commands in CI must use the same `uv` patterns as the Makefile:

```yaml
# CI Workflow Pattern
- name: Install dependencies
  run: make install-dev  # Uses uv sync internally

- name: Run quality checks  
  run: make quality      # Uses uv run prefix for all tools

- name: Run tests
  run: make ci-test      # Uses uv run pytest with CI-optimized flags
```

**Design Rationale**: Using `uv sync` instead of `uv pip install -e ".[dev]"` ensures identical dependency resolution between local and CI environments, preventing subtle version differences that could cause CI-only failures.

### Makefile Target Mapping

#### Core Development Workflow
- `make install-dev`: Complete development environment setup with all dependencies
- `make quality`: Comprehensive quality checks (linting, type checking, security)
- `make test`: Full test suite execution
- `make ci-test`: CI-optimized test execution (fail-fast, concise output)
- `make test-cov`: Test execution with coverage reporting
- `make test-integration`: Integration tests only

#### CI-Specific Targets
- `make pre-commit`: Pre-commit validation combining quality and fast tests
- `make validate`: Configuration and environment validation
- `make build`: Package building with proper artifact generation
- `make clean`: Cleanup of build artifacts and temporary files

#### Security and Auditing
- `make security`: Security vulnerability scanning with bandit
- `make audit`: Dependency vulnerability checking with safety and pip-audit

### Error Handling and Debugging

#### Identical Error Propagation
CI workflows must preserve the exact same error messages and exit codes as local Makefile execution:

```python
# Makefile ensures proper exit code propagation
quality:
    uv run ruff check .
    uv run mypy .
    uv run bandit -r src/
    # If any command fails, make fails with the same exit code
```

**Design Rationale**: Developers must be able to reproduce CI failures locally by running the exact same `make` command, with identical error output for efficient debugging.

#### Local CI Simulation
Developers can simulate the entire CI pipeline locally:

```bash
# Simulate CI workflow locally
make clean
make install-dev
make quality
make ci-test
make validate
make build
```

### Scripts Directory Integration

#### Current State
The `scripts/` directory contains utilities that must be properly integrated with Makefile targets:

- `scripts/validate_config.py` → Called via `make validate`
- `scripts/security_validation.py` → Called via `make security-validate`

#### Integration Strategy
Scripts are executed through Makefile targets rather than directly in CI:

```makefile
# Makefile integration
validate:
    uv run python scripts/validate_config.py

security-validate:
    uv run python scripts/security_validation.py
```

**Design Rationale**: This ensures that script execution uses the same environment and error handling as other development tasks, and allows for easy modification of script parameters or replacement without CI changes.

### Implementation Requirements

#### CI Workflow Structure
Each CI job must follow this pattern:

```yaml
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python and uv
        # ... setup steps
      - name: Install dependencies
        run: make install-dev
      - name: Run tests
        run: make ci-test

  quality:
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python and uv  
        # ... setup steps
      - name: Install dependencies
        run: make install-dev
      - name: Run quality checks
        run: make quality

  integration:
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python and uv
        # ... setup steps  
      - name: Install dependencies
        run: make install-dev
      - name: Run integration tests
        run: make test-integration
      - name: Validate configuration
        run: make validate
```

#### Makefile Requirements
The Makefile must support all CI operations and provide appropriate targets:

- All targets must work in CI environment (no interactive prompts)
- Proper exit code handling for all commands
- Environment variable support for CI-specific configuration
- Consistent `uv run` prefix for all Python commands
- Clear separation between development and CI-optimized targets

### Validation and Maintenance

#### Continuous Validation
The CI-Makefile alignment must be continuously validated:

1. **Local Testing**: All CI commands must be testable locally via `make` targets
2. **Error Consistency**: CI failures must produce identical errors to local execution
3. **Performance**: CI-specific targets should be optimized for CI environment constraints
4. **Documentation**: Clear documentation of which Makefile targets correspond to which CI jobs

#### Maintenance Strategy
Changes to build logic follow this pattern:

1. **Makefile First**: All changes made to Makefile targets
2. **Local Testing**: Verify changes work locally with `make` commands
3. **CI Inheritance**: CI automatically inherits changes without workflow modification
4. **Validation**: Confirm CI behavior matches local behavior

**Design Rationale**: This approach ensures that the Makefile remains the single source of truth for all build, test, and quality operations, while CI workflows remain stable and maintainable.