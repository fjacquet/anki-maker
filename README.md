# Document to Anki CLI

Convert documents to Anki flashcards using AI-powered content analysis.

## Overview

Document to Anki CLI is a comprehensive tool that transforms various document formats (PDF, DOCX, TXT, MD) into high-quality Anki flashcards using Google's Gemini Pro AI model. The application provides both CLI and web interfaces, allowing users to upload documents, preview and edit generated flashcards, and export them as Anki-compatible CSV files.

## Features

### ✅ Fully Implemented
- **Multi-Format Document Processing**: Support for PDF, DOCX, TXT, MD files, folders, and ZIP archives
- **Enhanced PDF Processing**: Robust handling of malformed, corrupted, or partially damaged PDFs with graceful error recovery
- **AI-Powered Flashcard Generation**: Gemini Pro model integration via litellm for intelligent content analysis
- **Dual Interface Support**: Both command-line and web interfaces available
- **Interactive Flashcard Management**: Preview, edit, delete, and add flashcards with rich formatting
- **Smart Text Processing**: Automatic text chunking to handle large documents within token limits
- **Multiple Card Types**: Generates both question-answer pairs and cloze deletion cards
- **Robust Error Handling**: Comprehensive error handling with actionable user guidance
- **CSV Export**: Anki-compatible CSV export with detailed statistics
- **Progress Tracking**: Real-time progress indicators for long-running operations
- **Session Management**: Web interface with session-based flashcard editing
- **Accessibility**: WCAG 2.1 AA compliant web interface with responsive design

## Installation

### Prerequisites
- Python 3.12+ (recommended 3.13+)
- Google Gemini API key
- uv package manager

### Quick Install

```bash
# Clone the repository
git clone <repository-url>
cd document-to-anki-cli

# Install dependencies using uv
uv sync

# Install in development mode (includes testing tools)
uv sync --all-extras
```

### Alternative Installation

```bash
# Using pip (if uv is not available)
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Configuration

### Environment Variables

The application requires configuration through environment variables. Create a `.env` file in the project root:

```bash
# Required: Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOGURU_LEVEL=INFO

# Optional: Model Configuration
MODEL=gemini/gemini-2.5-flash  # Default model (see supported models below)
OPENAI_API_KEY=your-openai-api-key-here  # Required for OpenAI models

# Optional: LLM Configuration
LITELLM_TIMEOUT=300  # Request timeout in seconds

# Supported Models:
# Gemini models (require GEMINI_API_KEY):
#   - gemini/gemini-2.5-flash (default, fastest)
#   - gemini/gemini-2.5-pro (more capable)
# OpenAI models (require OPENAI_API_KEY):
#   - openai/gpt-4o (latest GPT-4)
#   - openai/gpt-4 (standard GPT-4)
#   - openai/gpt-3.5-turbo (faster, lower cost)

# Optional: Web Interface Configuration
WEB_HOST=127.0.0.1  # Web server host
WEB_PORT=8000  # Web server port
```

### Getting API Keys

#### Gemini API Key (Default)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file as `GEMINI_API_KEY`

#### OpenAI API Key (Optional)
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in to your OpenAI account
3. Create a new API key
4. Copy the key to your `.env` file as `OPENAI_API_KEY`

## Usage

### Command Line Interface

#### Basic Document Conversion

```bash
# Convert a single document
document-to-anki input.pdf

# Specify output location
document-to-anki input.pdf --output my-flashcards.csv

# Process a folder of documents
document-to-anki documents/ --output folder-flashcards.csv

# Process a ZIP archive
document-to-anki archive.zip --output archive-flashcards.csv
```

#### Advanced CLI Options

```bash
# Skip interactive preview (batch mode)
document-to-anki input.pdf --no-preview --batch

# Enable verbose logging
document-to-anki input.pdf --verbose

# Batch process multiple files
document-to-anki batch-convert file1.pdf file2.docx folder/ --output-dir ./outputs/

# Show help
document-to-anki --help
```

#### Interactive Flashcard Management

When processing documents, the CLI provides an interactive menu for flashcard management:

- **Edit flashcards**: Modify question and answer content
- **Delete flashcards**: Remove unwanted cards
- **Add flashcards**: Create new cards manually
- **Preview flashcards**: View formatted card previews
- **Statistics**: View card counts and validation status
- **Export**: Generate Anki-compatible CSV files

### Web Interface

#### Starting the Web Server

```bash
# Start the web interface
document-to-anki-web

# Or specify host and port
uvicorn document_to_anki.web.app:app --host 0.0.0.0 --port 8080
```

#### Using the Web Interface

1. **Upload Documents**: Drag and drop files or click to browse
   - Supports single files, multiple files, folders, and ZIP archives
   - Real-time file validation and progress tracking

2. **Monitor Processing**: View real-time progress and status updates
   - Document text extraction progress
   - AI flashcard generation status
   - Error and warning notifications

3. **Manage Flashcards**: Interactive flashcard editing interface
   - Preview all generated flashcards
   - Edit questions and answers inline
   - Delete unwanted flashcards
   - Add new flashcards manually
   - Validate flashcard content

4. **Export Results**: Download Anki-compatible CSV files
   - Customizable filename
   - Detailed export statistics
   - Automatic file cleanup

### Python API

#### Basic Usage

```python
from document_to_anki.core.document_processor import DocumentProcessor
from document_to_anki.core.flashcard_generator import FlashcardGenerator

# Initialize components
doc_processor = DocumentProcessor()
flashcard_gen = FlashcardGenerator()

# Process documents
result = doc_processor.process_upload("path/to/document.pdf")

# Generate flashcards
flashcards_result = flashcard_gen.generate_flashcards(
    [result.text_content], 
    result.source_files
)

# Export to CSV
success, summary = flashcard_gen.export_to_csv("output.csv")
```

#### Advanced API Usage

```python
from pathlib import Path
from document_to_anki.core.llm_client import LLMClient
from document_to_anki.models.flashcard import Flashcard

# Custom LLM configuration
llm_client = LLMClient(model="gemini/gemini-2.5-flash", timeout=300)

# Generate flashcards directly from text
text = "Your educational content here..."
flashcard_data = llm_client.generate_flashcards_from_text_sync(text)

# Create flashcard objects
flashcards = []
for data in flashcard_data:
    flashcard = Flashcard.create(
        question=data["question"],
        answer=data["answer"],
        card_type=data["card_type"],
        source_file="manual_input"
    )
    flashcards.append(flashcard)

# Validate and export
valid_cards = [card for card in flashcards if card.validate_content()]
```

## Supported File Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| PDF | `.pdf` | Portable Document Format files (with enhanced malformed PDF support) |
| Word Document | `.docx` | Microsoft Word documents |
| Text File | `.txt` | Plain text files |
| Markdown | `.md` | Markdown formatted files |
| ZIP Archive | `.zip` | Archives containing supported formats |

### PDF Processing Features

The application includes advanced PDF processing capabilities:

- **Malformed PDF Support**: Automatically handles corrupted or non-standard PDFs using lenient parsing
- **Page-by-Page Processing**: Processes each page individually, allowing partial extraction from damaged files
- **Error Recovery**: Skips problematic pages and continues processing the rest of the document
- **Detailed Logging**: Shows which pages were successfully processed vs. skipped
- **Multiple Extraction Methods**: Falls back to alternative extraction methods when primary methods fail

### File Size Limits

- **Individual files**: 50MB maximum
- **ZIP archives**: 50MB maximum (total)
- **Text content**: No specific limit (chunked for AI processing)

## Development

### CI-Makefile Integration

This project maintains strict alignment between local development commands and CI pipeline execution. The GitHub Actions workflow uses the same Makefile targets that developers use locally, ensuring consistent behavior.

#### Makefile Targets Used in CI

| CI Job | Makefile Target | Purpose |
|--------|----------------|---------|
| **Setup** | `make install-dev` | Install dependencies with all extras |
| **Test** | `make test-cov` | Run tests with coverage reporting |
| **Quality** | `make ci-quality` | Run all quality checks with CI-friendly output |
| **Integration** | `make ci-test-integration` | Run integration tests in CI mode |
| **Validation** | `make validate` | Validate configuration and environment |
| **Build** | `make ci-build` | Build package with CI-friendly output |

#### Key CI Features

- **Consistent Commands**: CI uses identical logic to local development
- **Environment Validation**: Automatic detection of CI vs local environment
- **Error Handling**: Proper exit codes and error propagation
- **Output Format**: GitHub Actions-compatible output formatting
- **Dependency Management**: Uses `uv sync --all-extras` for complete setup

#### Local CI Testing

You can run the exact same commands locally that run in CI:

```bash
# Test the complete CI pipeline locally
make ci-setup && make ci-quality && make ci-test && make ci-validate && make ci-build

# Individual CI steps
make ci-setup     # Set up CI environment
make ci-quality   # Quality checks with GitHub Actions format
make ci-test      # Tests with CI-friendly output
make ci-validate  # Configuration validation
make ci-build     # Package build
```

#### Troubleshooting CI Issues

If CI fails but local tests pass, check:

1. **Environment Variables**: Ensure CI has required secrets (GEMINI_API_KEY)
2. **Dependencies**: Run `make ci-setup` locally to match CI environment
3. **Output Format**: Use `make ci-quality` to see GitHub Actions formatted output
4. **Exit Codes**: CI targets fail fast with proper exit codes

For detailed troubleshooting, see [CI-Makefile Troubleshooting](#ci-makefile-troubleshooting).

### Project Structure

```
document-to-anki-cli/
├── src/document_to_anki/          # Main package
│   ├── cli/                       # Command-line interface
│   │   └── main.py               # CLI entry point
│   ├── web/                       # Web interface
│   │   ├── app.py                # FastAPI application
│   │   ├── templates/            # HTML templates
│   │   └── static/               # CSS, JS, assets
│   ├── core/                      # Core business logic
│   │   ├── document_processor.py # Document handling
│   │   ├── flashcard_generator.py# Flashcard management
│   │   └── llm_client.py         # AI integration
│   ├── models/                    # Data models
│   │   └── flashcard.py          # Pydantic models
│   └── utils/                     # Utility modules
│       ├── file_handler.py       # File operations
│       └── text_extractor.py     # Text extraction
├── docs/                          # Documentation
│   ├── API.md                    # API reference
│   ├── CONFIGURATION.md          # Configuration guide
│   ├── EXAMPLES.md               # Usage examples
│   └── TROUBLESHOOTING.md        # Troubleshooting guide
├── tests/                         # Test suite
├── test_integration_check.py      # Integration test for model configuration
├── pyproject.toml                # Project configuration
└── README.md                     # This file
```

### Running Tests

The project uses a Makefile-based development workflow that ensures consistency between local development and CI environments.

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run tests with fail-fast (stops on first failure)
make test-fast

# Run integration tests only
make test-integration

# Run integration tests with coverage
make test-integration-cov

# CI-specific test execution (used in GitHub Actions)
make ci-test
make ci-test-integration

# Run integration test for model configuration
python test_integration_check.py

# Run web app startup validation test
python test_startup_validation.py
```

**Note**: All test commands use the `uv run` prefix internally for consistent virtual environment handling.

### Code Quality

The project uses Makefile targets that match the CI pipeline for consistent code quality checks:

```bash
# Run all quality checks (includes automatic formatting)
make quality

# Individual quality checks
make lint          # Run linting and auto-fix issues
make format        # Format code with ruff
make format-check  # Check formatting without changes
make type-check    # Run mypy type checking
make security      # Run bandit security scan
make audit         # Run dependency vulnerability check

# CI-specific quality checks (used in GitHub Actions)
make ci-quality

# Fix all auto-fixable issues
make fix
```

**CI Alignment**: The `make ci-quality` target uses GitHub Actions output format and is identical to what runs in CI, ensuring local and CI results match exactly.

### Development Workflow

The project uses a Makefile-based workflow that ensures consistency between local development and CI:

1. **Setup Development Environment**
   ```bash
   make setup        # Basic setup
   make setup-full   # Full setup with samples and environment
   # Or manually:
   make install-dev  # Install with all development dependencies
   ```

2. **Make Changes**
   - Follow the existing code style and patterns
   - Add comprehensive docstrings to all public methods
   - Include type hints for all function parameters and returns

3. **Test Changes**
   ```bash
   make test         # Run all tests
   make quality      # Run all quality checks (includes auto-formatting)
   make pre-commit   # Run full pre-commit validation
   ```

4. **CI-Compatible Commands**
   ```bash
   # These commands match exactly what runs in GitHub Actions:
   make ci-setup     # CI environment setup
   make ci-test      # CI test execution
   make ci-quality   # CI quality checks
   make ci-validate  # CI configuration validation
   make ci-build     # CI package build
   ```

5. **Submit Changes**
   - Ensure all tests pass: `make test`
   - Run quality checks: `make quality`
   - Update documentation if needed
   - Create descriptive commit messages

**CI Alignment**: All `make ci-*` targets use identical logic to GitHub Actions, ensuring local testing matches CI behavior exactly.

## API Reference

### Core Classes

#### DocumentProcessor
Handles document upload, validation, and text extraction.

**Key Methods:**
- `process_upload(upload_path)`: Process files, folders, or ZIP archives
- `validate_upload_path(path)`: Check if a path can be processed
- `get_supported_formats()`: Get list of supported file extensions

#### FlashcardGenerator
Manages flashcard creation, editing, and export functionality.

**Key Methods:**
- `generate_flashcards(text_content, source_files)`: Generate flashcards from text
- `preview_flashcards(console)`: Display rich-formatted flashcard preview
- `edit_flashcard(id, question, answer)`: Edit existing flashcard
- `delete_flashcard(id)`: Remove flashcard by ID
- `add_flashcard(question, answer, type)`: Add new flashcard manually
- `export_to_csv(output_path)`: Export flashcards to CSV format

#### LLMClient
Handles communication with Gemini LLM through litellm.

**Key Methods:**
- `generate_flashcards_from_text(text)`: Async flashcard generation
- `generate_flashcards_from_text_sync(text)`: Synchronous flashcard generation
- `chunk_text_for_processing(text, max_tokens)`: Split large text into chunks

### Data Models

#### Flashcard
Pydantic model representing a single flashcard.

**Fields:**
- `id`: Unique identifier
- `question`: Question text
- `answer`: Answer text
- `card_type`: "qa" or "cloze"
- `source_file`: Original file name
- `created_at`: Creation timestamp

**Methods:**
- `create(question, answer, card_type, source_file)`: Class method to create new flashcard
- `to_csv_row()`: Convert to Anki-compatible CSV format
- `validate_content()`: Check if flashcard content is valid

## Documentation

For detailed information, see the comprehensive documentation in the `docs/` folder:

- **[API Documentation](docs/API.md)** - Complete API reference for Python, REST, and CLI interfaces
- **[Configuration Guide](docs/CONFIGURATION.md)** - Environment variables, model selection, and advanced configuration
- **[Usage Examples](docs/EXAMPLES.md)** - Comprehensive examples for CLI, web interface, and Python API
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues, solutions, and debugging tips

## Quick Troubleshooting

### Common Issues

#### API Key Problems
```
Error: Failed to generate flashcards: API key not found
```
**Solution:** Ensure `GEMINI_API_KEY` is set in your `.env` file or environment variables.

#### File Processing Errors
```
Error: Unsupported file type: .xyz
```
**Solution:** Check that your files are in supported formats (PDF, DOCX, TXT, MD, ZIP).

#### Memory Issues
```
Error: Memory allocation failed
```
**Solutions:**
- Process smaller files or fewer files at once
- Close other applications to free memory
- Use batch processing mode for large document sets

#### Network Connectivity
```
Error: Failed to connect to AI service
```
**Solutions:**
- Check internet connection
- Verify API key is valid and has quota remaining
- Try again after a few minutes (rate limiting)

For complete troubleshooting information, see **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**.

### CI-Makefile Troubleshooting

If you encounter issues with CI-Makefile alignment:

```bash
# Test CI pipeline locally
make ci-setup && make ci-quality && make ci-test && make ci-validate && make ci-build

# Debug environment differences
make debug-env
make check-env

# Use CI-equivalent commands
make ci-quality  # Instead of individual quality tools
make ci-test     # Instead of direct pytest
```

See the [CI-Makefile Troubleshooting](docs/TROUBLESHOOTING.md#ci-makefile-troubleshooting) section for detailed guidance.

## Contributing

We welcome contributions! Please follow these guidelines:

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/document-to-anki-cli.git`
3. Create a virtual environment: `uv sync --all-extras`
4. Create a feature branch: `git checkout -b feature/amazing-feature`

### Code Standards

- **Python Style**: Follow PEP 8, enforced by ruff
- **Type Hints**: Include type hints for all public methods
- **Docstrings**: Use Google-style docstrings for all public classes and methods
- **Testing**: Maintain >80% test coverage
- **Error Handling**: Provide clear, actionable error messages

### Submitting Changes

1. Add tests for new functionality
2. Ensure all tests pass: `uv run pytest`
3. Check code quality: `uv run ruff check && uv run mypy src/`
4. Update documentation if needed
5. Commit with descriptive messages
6. Push to your fork: `git push origin feature/amazing-feature`
7. Open a Pull Request with detailed description

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Changelog

### Version 0.1.0 (Current)
- ✅ Complete CLI interface with interactive flashcard management
- ✅ Full-featured web interface with drag-and-drop uploads
- ✅ Support for PDF, DOCX, TXT, MD files and ZIP archives
- ✅ **Enhanced PDF Processing**: Robust handling of malformed and corrupted PDFs
  - Graceful error recovery with page-by-page processing
  - Automatic fallback to lenient parsing mode
  - Detailed logging of successful vs. failed page processing
  - Continues processing even when individual pages fail
- ✅ Gemini Pro AI integration for intelligent flashcard generation
- ✅ Rich progress tracking and error handling
- ✅ Comprehensive test suite with >80% coverage
- ✅ Accessible, responsive web design (WCAG 2.1 AA)
- ✅ Session-based flashcard editing and management
- ✅ Anki-compatible CSV export with detailed statistics
- ✅ **Improved Development Setup**: Enhanced `make install-dev` to use `--all-extras` for complete dependency installation
- ✅ **Enhanced Development Workflow**: Updated Makefile to automatically format code during quality checks
  - `make quality`, `make format`, and `make lint` now automatically apply formatting fixes
  - Improves developer experience by eliminating manual formatting steps
  - Ensures consistent code style across the project
- ✅ **Improved Documentation Structure**: Organized all documentation into `docs/` folder
  - Moved API.md, CONFIGURATION.md, EXAMPLES.md, and TROUBLESHOOTING.md to docs/
  - Added comprehensive documentation index (docs/README.md)
  - Updated all cross-references and navigation links
  - Enhanced project organization and documentation discoverability
- ✅ **CI-Makefile Integration**: Complete alignment between local development and CI pipeline
  - GitHub Actions workflow uses identical Makefile targets as local development
  - CI-specific targets (`ci-setup`, `ci-test`, `ci-quality`, `ci-validate`, `ci-build`) for optimized CI execution
  - Consistent `uv run` usage throughout all commands
  - Enhanced error handling and exit codes for proper CI integration
  - Comprehensive troubleshooting guide for CI-Makefile issues

## CI-Makefile Alignment Summary

This project maintains strict consistency between local development and CI environments through:

### Aligned Commands
- **Local**: `make test` → **CI**: `make test-cov`
- **Local**: `make quality` → **CI**: `make ci-quality`
- **Local**: `make validate` → **CI**: `make validate`
- **Local**: `make build` → **CI**: `make ci-build`

### Key Benefits
- **Predictable Results**: Local testing matches CI behavior exactly
- **Easy Debugging**: Run CI commands locally to reproduce issues
- **Consistent Environment**: Same `uv run` prefix and error handling
- **Maintainable**: Single source of truth for all development workflows

### Quick CI Testing
```bash
# Test the complete CI pipeline locally
make ci-setup && make ci-quality && make ci-test && make ci-validate && make ci-build
```

For detailed information, see the [CI-Makefile Integration](#ci-makefile-integration) section and [CI-Makefile Troubleshooting](docs/TROUBLESHOOTING.md#ci-makefile-troubleshooting).

## Acknowledgments

- **Google Gemini**: AI model for intelligent content analysis
- **litellm**: Unified LLM API interface
- **FastAPI**: Modern web framework for the API
- **Rich**: Enhanced terminal output and formatting
- **Click**: Command-line interface framework
- **Pydantic**: Data validation and serialization
- **pytest**: Testing framework
