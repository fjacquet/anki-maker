# Document to Anki CLI

Convert documents to Anki flashcards using AI-powered content analysis.

## Overview

Document to Anki CLI is a powerful tool that transforms various document formats (PDF, DOCX, TXT) into high-quality Anki flashcards using Google's Gemini Pro AI model. The tool intelligently analyzes document content and generates both question-answer pairs and cloze deletion cards optimized for effective learning and retention.

## Features

### ✅ Implemented
- **LLM Integration**: Gemini Pro model integration via litellm for intelligent flashcard generation
- **Smart Text Processing**: Automatic text chunking to handle large documents within token limits
- **Multiple Card Types**: Generates both Q&A pairs and cloze deletion cards
- **Robust Error Handling**: Exponential backoff retry logic for API failures
- **Flexible API**: Both async and synchronous interfaces available

### 🚧 In Development
- Document parsing (PDF, DOCX, TXT)
- Anki deck export functionality
- CLI interface
- Web interface
- Configuration management

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd anki-maker

# Install dependencies using uv
uv sync

# Or install in development mode
uv sync --dev
```

## Usage

### LLM Client (Available Now)

```python
from src.document_to_anki.core.llm_client import LLMClient

# Initialize the client
client = LLMClient(model="gemini/gemini-pro")

# Generate flashcards from text (async)
flashcards = await client.generate_flashcards_from_text("Your document content here...")

# Or use the synchronous version
flashcards = client.generate_flashcards_from_text_sync("Your document content here...")

# Each flashcard contains:
# - question: The question or cloze deletion text
# - answer: The answer
# - card_type: "qa" or "cloze"
```

### CLI (Coming Soon)

```bash
# Convert a document to Anki deck
document-to-anki input.pdf --output my-deck.apkg

# Process multiple documents
document-to-anki docs/*.pdf --output-dir ./anki-decks/
```

## Configuration

The tool requires a Gemini API key. Set it as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_llm_client.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Fix linting issues
uv run ruff check --fix
```

## Architecture

The project follows a modular architecture:

- **Core**: Business logic and AI integration (`src/document_to_anki/core/`)
- **CLI**: Command-line interface (`src/document_to_anki/cli/`)
- **Web**: Web interface (`src/document_to_anki/web/`)
- **Tests**: Comprehensive test suite (`tests/`)

### Key Components

- **LLMClient**: Handles AI model communication and flashcard generation
- **Document Parsers**: Extract text from various document formats (planned)
- **Anki Exporters**: Generate Anki-compatible deck files (planned)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`uv run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Requirements

- Python 3.13+
- Google Gemini API access
- Dependencies managed via `uv`

## License

[Add your license information here]

## Roadmap

- [x] LLM client implementation with Gemini integration
- [ ] Document parsing for PDF, DOCX, and TXT files
- [ ] Anki deck export functionality
- [ ] CLI interface with rich output
- [ ] Web interface for easy document upload
- [ ] Batch processing capabilities
- [ ] Configuration file support
- [ ] Advanced prompt customization
