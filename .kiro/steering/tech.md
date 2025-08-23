# Technology Stack

## Core Technologies

- **Python**: 3.12+ (recommended 3.13+)
- **Package Manager**: uv (primary), pip (fallback)
- **Framework**: Click for CLI, FastAPI for web interface
- **AI Integration**: litellm with Google Gemini Pro
- **Data Models**: Pydantic for validation and serialization
- **Configuration**: pydantic-settings with .env support

## Key Dependencies

### Core Libraries
- `click>=8.2.1` - CLI framework
- `fastapi>=0.115.14` - Web API framework
- `uvicorn>=0.35.0` - ASGI server
- `pydantic>=2.9.0` - Data validation
- `python-dotenv>=1.1.1` - Environment configuration
- `litellm>=1.73.6` - LLM integration
- `rich>=14.1.0` - Terminal formatting
- `loguru>=0.7.2` - Logging

### Document Processing
- `PyPDF2>=3.0.0` - PDF processing
- `python-docx>=1.1.0` - DOCX processing
- `pandas>=2.3.2` - CSV export
- `numpy>=1.24.0` - Data processing

### Development Tools
- `pytest>=8.4.1` - Testing framework
- `ruff>=0.1.0` - Linting and formatting
- `mypy>=1.17.1` - Type checking
- `bandit>=1.8.6` - Security scanning
- `safety>=3.2.4` - Dependency auditing

## Build System

### Package Configuration
- **Build System**: setuptools via pyproject.toml
- **Entry Points**: 
  - `document-to-anki` - Main CLI command
  - `document-to-anki-web` - Web server command
  - `anki-maker` - Alternative CLI alias

### Development Scripts
All commands use `uv run` prefix for consistency:

```bash
# Installation
make install          # Install package
make install-dev      # Install with dev dependencies

# Testing
make test            # Run all tests
make test-cov        # Run with coverage
make test-fast       # Run with fail-fast
make test-integration # Integration tests only

# Code Quality
make lint            # Run linting
make lint-fix        # Fix linting issues
make format          # Format code
make type-check      # Run mypy
make security        # Run bandit
make quality         # Run all quality checks

# Development
make setup           # Set up dev environment
make run-cli         # Run CLI in dev mode
make run-web         # Run web server in dev mode
make clean           # Clean build artifacts
```

## Configuration Management

### Environment Variables
Required configuration via `.env` file:
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `MODEL` - LLM model (default: gemini/gemini-2.5-flash)
- `LOG_LEVEL` - Logging level (default: INFO)

### Supported Models
- `gemini/gemini-2.5-flash` (default)
- `gemini/gemini-2.5-pro`
- `openai/gpt-4*` variants (requires OPENAI_API_KEY)

## Code Quality Standards

### Linting & Formatting
- **Ruff**: Primary linter and formatter
- **Line Length**: 110 characters
- **Python Version**: 3.12+ target
- **Import Sorting**: isort via ruff
- **Quote Style**: Double quotes

### Type Checking
- **MyPy**: Strict type checking enabled
- **Type Hints**: Required for all public methods
- **Disallow Untyped**: Functions must have type annotations

### Testing
- **Framework**: pytest with asyncio support
- **Coverage**: Minimum 80% required
- **Markers**: integration, slow, cli, web, e2e
- **Fixtures**: Comprehensive test fixtures in conftest.py

### Security
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking
- **Pip-audit**: Additional dependency auditing

## Architecture Patterns

### Project Structure
```
src/document_to_anki/
├── cli/           # Command-line interface
├── web/           # FastAPI web application
├── core/          # Business logic
├── models/        # Pydantic data models
├── utils/         # Utility modules
└── config.py      # Configuration management
```

### Error Handling
- Custom exception classes for each module
- Comprehensive error messages with actionable guidance
- Graceful degradation and user-friendly error reporting

### Logging
- Loguru for structured logging
- Configurable log levels
- Rich console output for CLI
- Separate logging for web interface

## Development Workflow

1. **Setup**: `make setup` or `uv sync --group dev`
2. **Quality**: `make quality` before commits
3. **Testing**: `make test` for full test suite
4. **Pre-commit**: `make pre-commit` for final checks