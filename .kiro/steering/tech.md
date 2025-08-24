---
inclusion: always
---

# Technology Stack & Development Standards

## Core Stack
- **Python 3.12+** with `uv` package manager (use `uv run` for all commands)
- **CLI**: Click framework with Rich formatting
- **Web**: FastAPI with Uvicorn ASGI server
- **AI**: litellm client with Google Gemini Pro (default: `gemini/gemini-2.5-flash`)
- **Data**: Pydantic models for validation, pandas for CSV export
- **Config**: pydantic-settings with `.env` support

## Critical Dependencies
- **Testing**: `pytest` with `pytest-mock` (NEVER use `unittest.mock`)
- **Quality**: `ruff` (linting/formatting), `mypy` (type checking), `bandit` (security)
- **Document Processing**: `pypdf`, `python-docx`, support for PDF/DOCX/TXT/MD
- **Logging**: `loguru` for structured logging

## Development Commands
```bash
make setup           # Initial setup
make test           # Run all tests  
make quality        # Run all quality checks
make lint-fix       # Auto-fix linting issues
make run-cli        # Dev CLI mode
make run-web        # Dev web server
```

## Code Standards
- **Line length**: 110 characters
- **Type hints**: Required for all public methods
- **Imports**: Use ruff for sorting, prefer explicit imports
- **Quotes**: Double quotes consistently
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error handling**: Custom exceptions with actionable messages

## Architecture Rules
- **Structure**: `src/document_to_anki/{cli,web,core,models,utils}`
- **Entry points**: `document-to-anki` (CLI), `document-to-anki-web` (server)
- **Dependencies**: Inject at boundaries, mock external systems in tests
- **Async**: Use for I/O operations, handle exceptions properly
- **Configuration**: Validate with Pydantic, support env vars and files

## Testing Requirements
- **Coverage**: Minimum 80%
- **Mocking**: Use `pytest-mock` for external dependencies (LLM, file system)
- **Markers**: `@pytest.mark.integration`, `@pytest.mark.slow`
- **Independence**: Tests must not depend on execution order
- **Speed**: Unit tests < 5 seconds

## Security & Environment
- **API Keys**: Store in `.env`, never log or expose in errors
- **Input validation**: Sanitize all user inputs with Pydantic
- **File handling**: Validate paths, limit sizes, check types
- **Required env**: `GEMINI_API_KEY` (required), `MODEL`, `LOG_LEVEL`

## Design Principles
- **KISS**: Keep implementations simple and readable
- **DRY**: Avoid code duplication, extract common patterns
- **YAGNI**: Don't build features until needed
- **Use frameworks**: Leverage Click, FastAPI, Pydantic instead of custom solutions
