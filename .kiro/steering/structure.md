# Project Structure

## Root Directory Layout

```
document-to-anki-cli/
├── src/document_to_anki/          # Main package source code
├── tests/                         # Test suite
├── scripts/                       # Development and utility scripts
├── examples/                      # Sample documents and usage examples
├── exports/                       # Default output directory for CSV files
├── .kiro/                         # Kiro IDE configuration and specs
├── pyproject.toml                 # Project configuration and dependencies
├── Makefile                       # Development workflow commands
├── .env.example                   # Environment configuration template
└── README.md                      # Comprehensive project documentation
```

## Source Code Organization

### Main Package (`src/document_to_anki/`)

```
src/document_to_anki/
├── __init__.py                    # Package exports and version info
├── config.py                      # Configuration management and validation
├── cli/                           # Command-line interface
│   ├── __init__.py
│   └── main.py                    # CLI entry point with Click commands
├── web/                           # Web interface (FastAPI)
│   ├── __init__.py
│   ├── app.py                     # FastAPI application and routes
│   ├── templates/                 # Jinja2 HTML templates
│   └── static/                    # CSS, JavaScript, and assets
├── core/                          # Business logic modules
│   ├── __init__.py
│   ├── document_processor.py      # Document upload and text extraction
│   ├── flashcard_generator.py     # Flashcard creation and management
│   └── llm_client.py             # LLM integration via litellm
├── models/                        # Data models and schemas
│   ├── __init__.py
│   └── flashcard.py              # Pydantic models for flashcards
└── utils/                         # Utility modules
    ├── __init__.py
    ├── file_handler.py           # File operations and validation
    └── text_extractor.py         # Text extraction from various formats
```

## Test Organization

### Test Suite (`tests/`)

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and pytest configuration
├── fixtures/                     # Test data and sample files
├── test_cli_integration.py       # CLI interface integration tests
├── test_web_integration.py       # Web API integration tests
├── test_end_to_end.py            # Full workflow end-to-end tests
├── test_document_processor.py    # Document processing unit tests
├── test_flashcard_generator.py   # Flashcard generation unit tests
├── test_llm_client.py            # LLM client unit tests
├── test_file_handler.py          # File handling unit tests
├── test_text_extractor.py        # Text extraction unit tests
└── test_model_config.py          # Configuration validation tests
```

## Configuration Files

### Development Configuration
- **pyproject.toml**: Primary project configuration (dependencies, build system, tool configs)
- **Makefile**: Development workflow automation
- **.env.example**: Environment variable template
- **mypy.ini**: Type checking configuration (legacy, migrating to pyproject.toml)
- **.pre-commit-config.yaml**: Pre-commit hooks configuration

### IDE and Tooling
- **.kiro/**: Kiro IDE configuration and specifications
- **.vscode/**: VS Code settings (if present)
- **.gitignore**: Git ignore patterns
- **uv.lock**: Dependency lock file for reproducible builds

## Module Responsibilities

### CLI Module (`cli/`)
- Command-line argument parsing with Click
- Interactive user prompts and menus
- Rich console output and progress indicators
- Error handling with actionable guidance
- Integration with core business logic

### Web Module (`web/`)
- FastAPI REST API endpoints
- HTML template rendering with Jinja2
- Session management for flashcard editing
- File upload handling with validation
- Real-time progress updates via WebSocket/SSE

### Core Module (`core/`)
- **DocumentProcessor**: File validation, text extraction, batch processing
- **FlashcardGenerator**: AI-powered flashcard creation, editing, CSV export
- **LLMClient**: LLM integration, text chunking, retry logic

### Models Module (`models/`)
- **Flashcard**: Pydantic model for flashcard data
- **ProcessingResult**: Results from document processing operations
- Data validation and serialization schemas

### Utils Module (`utils/`)
- **FileHandler**: File system operations, format detection
- **TextExtractor**: Format-specific text extraction (PDF, DOCX, etc.)
- Shared utility functions and helpers

## Naming Conventions

### Files and Directories
- **Snake case**: All Python files use snake_case naming
- **Lowercase**: Directory names are lowercase
- **Descriptive**: Names clearly indicate purpose and scope

### Python Code
- **Classes**: PascalCase (e.g., `DocumentProcessor`, `FlashcardGenerator`)
- **Functions/Methods**: snake_case (e.g., `process_upload`, `generate_flashcards`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_MODEL`, `MAX_FILE_SIZE`)
- **Private**: Leading underscore for internal functions (e.g., `_handle_error`)

### Configuration
- **Environment Variables**: UPPER_SNAKE_CASE (e.g., `GEMINI_API_KEY`)
- **Config Keys**: snake_case in code, kebab-case in CLI options

## Import Organization

### Import Order (enforced by ruff)
1. Standard library imports
2. Third-party library imports
3. Local application imports (relative imports last)

### Import Style
- Absolute imports preferred over relative
- Explicit imports over wildcard imports
- Group related imports together

## Entry Points

### CLI Commands
- `document-to-anki` - Main CLI command
- `document-to-anki-web` - Web server launcher
- `anki-maker` - Alternative CLI alias

### Python API
- Import from `document_to_anki` package
- Core classes available at package level
- Submodules accessible for advanced usage

## Output and Artifacts

### Generated Files
- **CSV exports**: Anki-compatible flashcard files in `exports/` or specified directory
- **Logs**: Application logs (configurable location)
- **Cache**: Temporary processing files in `.cache/` (if caching enabled)

### Build Artifacts
- **dist/**: Package distribution files
- **build/**: Build intermediates
- **htmlcov/**: Coverage reports
- **__pycache__/**: Python bytecode cache