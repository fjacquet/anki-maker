# Document to Anki CLI - Usage Examples

This document provides comprehensive examples of how to use the Document to Anki CLI application in various scenarios.

## Prerequisites

1. Install the application:
   ```bash
   uv pip install -e .
   ```

2. Set up your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and preferences
   ```

3. Ensure you have a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## CLI Usage Examples

### Basic Usage

#### Convert a single PDF file
```bash
document-to-anki input.pdf --output flashcards.csv
```

#### Convert multiple files
```bash
document-to-anki file1.pdf file2.docx file3.txt --output combined_flashcards.csv
```

#### Process a folder of documents
```bash
document-to-anki /path/to/documents/ --output folder_flashcards.csv
```

#### Process a ZIP archive
```bash
document-to-anki documents.zip --output archive_flashcards.csv
```

### Advanced CLI Options

#### Enable verbose logging
```bash
document-to-anki input.pdf --verbose --output flashcards.csv
```

#### Specify custom model
```bash
document-to-anki input.pdf --model gemini/gemini-pro --output flashcards.csv
```

#### Set maximum number of flashcards
```bash
document-to-anki input.pdf --max-cards 50 --output flashcards.csv
```

#### Interactive mode with preview and editing
```bash
document-to-anki input.pdf --interactive --output flashcards.csv
```

#### Batch processing with custom settings
```bash
document-to-anki *.pdf --batch-size 5 --output batch_flashcards.csv
```

### CLI Help
```bash
# Get general help
document-to-anki --help

# Get help for specific commands
document-to-anki convert --help
```

## Web Interface Usage

### Starting the Web Server

#### Development mode
```bash
document-to-anki-web --dev
```

#### Production mode
```bash
document-to-anki-web --host 0.0.0.0 --port 8000
```

#### Custom configuration
```bash
document-to-anki-web --config /path/to/config.env
```

### Web Interface Workflow

1. **Upload Documents**
   - Drag and drop files onto the upload area
   - Or click "Choose Files" to select documents
   - Supports: PDF, DOCX, TXT, MD files, folders, and ZIP archives

2. **Configure Processing**
   - Select AI model (Gemini Pro, GPT-4, etc.)
   - Set number of flashcards to generate
   - Choose flashcard types (Q&A, Cloze deletion, or both)

3. **Generate Flashcards**
   - Click "Generate Flashcards"
   - Monitor progress with real-time updates
   - View processing logs if needed

4. **Review and Edit**
   - Preview generated flashcards
   - Edit questions and answers inline
   - Delete unwanted flashcards
   - Add custom flashcards manually

5. **Export**
   - Download as Anki-compatible CSV
   - Choose export format and options

## Configuration Examples

### Environment Variables

#### Basic configuration (.env)
```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional customizations
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100
FLASHCARDS_PER_CHUNK=15
```

#### Advanced configuration
```bash
# LLM Settings
MODEL=gemini/gemini-pro
LLM_MAX_RETRIES=5
LLM_TIMEOUT=60

# Performance
WORKER_PROCESSES=8
MEMORY_LIMIT_MB=1024
ENABLE_CACHING=true

# File Processing
SUPPORTED_EXTENSIONS=.pdf,.docx,.txt,.md,.rtf
TEMP_DIR=/tmp/anki_processing
CLEANUP_TEMP_FILES=true

# Export Settings
OUTPUT_DIR=./my_flashcards
CSV_DELIMITER=;
INCLUDE_METADATA=true
```

## Development Examples

### Running Tests
```bash
# Run all tests
uv run test

# Run with coverage
uv run test-cov

# Run only unit tests
uv run test tests/unit/

# Run integration tests
uv run test -m integration
```

### Code Quality Checks
```bash
# Run all quality checks
uv run quality

# Individual checks
uv run lint
uv run ruff format --check  # Check formatting without modifying files
uv run type-check
uv run security

# Or use make targets (note: make format automatically modifies files)
make lint      # Includes automatic formatting
make format    # Automatically formats code
make quality   # Runs all checks including automatic formatting
```

### Development Server
```bash
# CLI development
uv run dev-cli input.pdf --output test.csv

# Web development server
uv run dev-web
```

## Integration Examples

### Python API Usage

```python
from document_to_anki.core.document_processor import DocumentProcessor
from document_to_anki.core.flashcard_generator import FlashcardGenerator
from document_to_anki.config import settings

# Initialize components
processor = DocumentProcessor()
generator = FlashcardGenerator()

# Process a document
text_content = processor.process_upload("document.pdf")

# Generate flashcards
flashcards = generator.generate_flashcards(text_content)

# Export to CSV
generator.export_to_csv(flashcards, "output.csv")
```

### Custom Configuration

```python
from document_to_anki.config import Settings

# Custom settings
custom_settings = Settings(
    model="openai/gpt-4",
    max_tokens_per_request=8000,
    flashcards_per_chunk=20,
    log_level="DEBUG"
)

# Use custom settings
processor = DocumentProcessor(settings=custom_settings)
```

## Troubleshooting Examples

### Common Issues and Solutions

#### API Key Issues
```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Test API connection
document-to-anki --test-api
```

#### File Processing Issues
```bash
# Enable verbose logging
document-to-anki input.pdf --verbose --log-level DEBUG

# Check file permissions
ls -la input.pdf

# Test with a simple text file first
echo "Test content for flashcard generation." > test.txt
document-to-anki test.txt --output test.csv
```

#### Memory Issues with Large Files
```bash
# Reduce batch size
document-to-anki large_file.pdf --batch-size 1 --output flashcards.csv

# Use streaming mode
document-to-anki large_file.pdf --stream --output flashcards.csv
```

#### Web Interface Issues
```bash
# Check if port is available
lsof -i :8000

# Run with different port
document-to-anki-web --port 8080

# Check logs
document-to-anki-web --log-level DEBUG
```

## Performance Optimization Examples

### Large Document Processing
```bash
# Optimize for large files
export WORKER_PROCESSES=8
export MEMORY_LIMIT_MB=2048
export ENABLE_CACHING=true

document-to-anki large_document.pdf --output flashcards.csv
```

### Batch Processing Optimization
```bash
# Process multiple files efficiently
document-to-anki *.pdf \
  --batch-size 3 \
  --parallel \
  --cache-results \
  --output batch_flashcards.csv
```

## Export Format Examples

### Anki Import Format
The generated CSV files are compatible with Anki's import feature:

```csv
Question,Answer,Type,Source
"What is photosynthesis?","The process by which plants convert light energy into chemical energy","qa","biology.pdf"
"Plants convert {{c1::light energy}} into {{c1::chemical energy}} through photosynthesis","","cloze","biology.pdf"
```

### Custom Export Formats
```bash
# Tab-separated values
export CSV_DELIMITER=$'\t'
document-to-anki input.pdf --output flashcards.tsv

# Include additional metadata
export INCLUDE_METADATA=true
document-to-anki input.pdf --output flashcards_with_metadata.csv
```

## Automation Examples

### Bash Script for Batch Processing
```bash
#!/bin/bash
# process_documents.sh

INPUT_DIR="./documents"
OUTPUT_DIR="./flashcards"

mkdir -p "$OUTPUT_DIR"

for file in "$INPUT_DIR"/*.pdf; do
    filename=$(basename "$file" .pdf)
    echo "Processing $filename..."
    
    document-to-anki "$file" \
        --output "$OUTPUT_DIR/${filename}_flashcards.csv" \
        --verbose
done

echo "Batch processing complete!"
```

### Cron Job for Regular Processing
```bash
# Add to crontab (crontab -e)
# Process new documents daily at 2 AM
0 2 * * * /path/to/process_documents.sh >> /var/log/anki_processing.log 2>&1
```

### GitHub Actions Workflow
```yaml
name: Generate Flashcards
on:
  push:
    paths: ['documents/**']

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e .
      - name: Generate flashcards
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          document-to-anki documents/ --output flashcards.csv
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: flashcards
          path: flashcards.csv
```

This comprehensive guide should help users get started with the Document to Anki CLI application and explore its various features and capabilities.