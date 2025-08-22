# Usage Examples

This document provides comprehensive examples of using Document to Anki CLI in various scenarios.

## Table of Contents

- [Basic CLI Usage](#basic-cli-usage)
- [Advanced CLI Features](#advanced-cli-features)
- [Web Interface Examples](#web-interface-examples)
- [Python API Examples](#python-api-examples)
- [Batch Processing](#batch-processing)
- [Configuration Examples](#configuration-examples)
- [Integration Examples](#integration-examples)

## Basic CLI Usage

### Convert a Single PDF Document

```bash
# Basic conversion
document-to-anki lecture-notes.pdf

# Specify output location
document-to-anki lecture-notes.pdf --output my-flashcards.csv

# Skip interactive preview (automated mode)
document-to-anki lecture-notes.pdf --no-preview --batch
```

### Process Different File Types

```bash
# Word document
document-to-anki research-paper.docx --output research-cards.csv

# Text file
document-to-anki study-notes.txt --output study-cards.csv

# Markdown file
document-to-anki README.md --output readme-cards.csv
```

### Process Multiple Files

```bash
# Process a folder of documents
document-to-anki documents/ --output folder-flashcards.csv

# Process a ZIP archive
document-to-anki course-materials.zip --output course-cards.csv
```

### Interactive Flashcard Management

When you run without `--no-preview`, you'll get an interactive menu:

```bash
document-to-anki textbook-chapter.pdf
```

This opens an interactive session where you can:
- **Edit flashcards**: Modify questions and answers
- **Delete flashcards**: Remove unwanted cards
- **Add flashcards**: Create new cards manually
- **Preview flashcards**: View all cards with formatting
- **Show statistics**: See card counts and validation status

Example interaction:
```
📚 Flashcard Management Menu (25 cards)
┌─────────────────────────────────────────────┐
│  e - ✏️  Edit a flashcard                │
│  d - 🗑️  Delete a flashcard              │
│  a - ➕ Add a new flashcard             │
│  p - 👀 Preview flashcards again        │
│  s - 📊 Show statistics                 │
│  c - ✅ Continue to export              │
│  q - ❌ Quit without saving             │
└─────────────────────────────────────────────┘
What would you like to do? [c]: e

Available flashcards:
  1. [a1b2c3d4] ✓ What is the capital of France?
  2. [e5f6g7h8] ✓ Define photosynthesis...
  3. [i9j0k1l2] ⚠️ The process of {{c1::mitosis}} involves...

Enter flashcard number or ID (or 'cancel' to go back): 1

Editing flashcard a1b2c3d4...
Type: QA
Source: textbook-chapter.pdf
Current Question: What is the capital of France?
Current Answer: Paris

Proceed with editing this flashcard? [Y/n]: y

Enter new content (press Enter to keep current):
New question [What is the capital of France?]: What is the capital city of France?
New answer [Paris]: Paris, the largest city in France

Preview of changes:
Question will change to: What is the capital city of France?

Save these changes? [Y/n]: y
✓ Flashcard a1b2c3d4... updated successfully
```

## Advanced CLI Features

### Verbose Logging

```bash
# Enable detailed logging
document-to-anki complex-document.pdf --verbose

# This shows:
# - File processing steps
# - Text extraction progress
# - AI generation details
# - Error diagnostics
```

### Batch Processing Multiple Files

```bash
# Process multiple specific files
document-to-anki batch-convert file1.pdf file2.docx folder/ --output-dir ./outputs/

# This creates:
# - ./outputs/file1_flashcards.csv
# - ./outputs/file2_flashcards.csv
# - ./outputs/folder_flashcards.csv
```

### Automated Workflows

```bash
# Fully automated processing (no user interaction)
document-to-anki documents/ --no-preview --batch --output automated-cards.csv

# Perfect for scripts and automation
```

## Web Interface Examples

### Starting the Web Server

```bash
# Default configuration (localhost:8000)
document-to-anki-web

# Custom host and port
uvicorn document_to_anki.web.app:app --host 0.0.0.0 --port 8080 --reload
```

### Web Interface Workflow

1. **Upload Files**
   - Drag and drop files onto the upload area
   - Or click "Choose Files" to browse
   - Supports: single files, multiple files, folders, ZIP archives
   - Real-time validation shows supported/unsupported files

2. **Monitor Processing**
   ```
   Processing Status: 45%
   ⏳ Generating flashcards with AI...
   
   Files processed: 3/5
   Flashcards generated: 127
   Estimated time remaining: 2 minutes
   ```

3. **Manage Flashcards**
   - Interactive table showing all flashcards
   - Click to edit questions and answers inline
   - Delete unwanted flashcards
   - Add new flashcards manually
   - Real-time validation feedback

4. **Export Results**
   - Download as CSV file
   - Customizable filename
   - Detailed export statistics

### API Endpoints

The web interface exposes REST API endpoints:

```bash
# Upload files
curl -X POST "http://localhost:8000/api/upload" \
  -F "files=@document.pdf"

# Check processing status
curl "http://localhost:8000/api/status/{session_id}"

# Get flashcards
curl "http://localhost:8000/api/flashcards/{session_id}"

# Edit a flashcard
curl -X PUT "http://localhost:8000/api/flashcards/{session_id}/{flashcard_id}" \
  -H "Content-Type: application/json" \
  -d '{"question": "New question", "answer": "New answer"}'

# Export to CSV
curl -X POST "http://localhost:8000/api/export/{session_id}" \
  -H "Content-Type: application/json" \
  -d '{"filename": "my-flashcards.csv"}' \
  --output flashcards.csv
```

## Python API Examples

### Basic Document Processing

```python
from pathlib import Path
from document_to_anki.core.document_processor import DocumentProcessor
from document_to_anki.core.flashcard_generator import FlashcardGenerator

# Initialize components
doc_processor = DocumentProcessor()
flashcard_gen = FlashcardGenerator()

# Process a document
result = doc_processor.process_upload("textbook.pdf")
print(f"Extracted {result.total_characters} characters from {result.file_count} files")

# Generate flashcards
flashcards_result = flashcard_gen.generate_flashcards(
    [result.text_content], 
    result.source_files
)

print(f"Generated {flashcards_result.flashcard_count} flashcards")
print(f"Processing took {flashcards_result.processing_time:.2f} seconds")

# Export to CSV
success, summary = flashcard_gen.export_to_csv(Path("output.csv"))
if success:
    print(f"Exported {summary['exported_flashcards']} flashcards")
    print(f"File size: {summary['file_size_bytes']} bytes")
```

### Advanced Flashcard Management

```python
from document_to_anki.models.flashcard import Flashcard
from document_to_anki.core.flashcard_generator import FlashcardGenerator

# Create flashcard generator
gen = FlashcardGenerator()

# Add flashcards manually
flashcard1, msg1 = gen.add_flashcard(
    question="What is the capital of France?",
    answer="Paris",
    card_type="qa",
    source_file="geography.txt"
)

flashcard2, msg2 = gen.add_flashcard(
    question="The capital of France is {{c1::Paris}}",
    answer="Paris",
    card_type="cloze",
    source_file="geography.txt"
)

print(f"Added flashcard 1: {msg1}")
print(f"Added flashcard 2: {msg2}")

# Edit a flashcard
success, msg = gen.edit_flashcard(
    flashcard1.id,
    "What is the capital city of France?",
    "Paris, the largest city in France"
)
print(f"Edit result: {msg}")

# Get statistics
stats = gen.get_statistics()
print(f"Total cards: {stats['total_count']}")
print(f"Valid cards: {stats['valid_count']}")
print(f"Q&A cards: {stats['qa_count']}")
print(f"Cloze cards: {stats['cloze_count']}")

# Validate all flashcards
valid_cards, invalid_cards = gen.validate_all_flashcards()
print(f"Validation: {len(valid_cards)} valid, {len(invalid_cards)} invalid")
```

### Custom LLM Configuration

```python
from document_to_anki.core.llm_client import LLMClient
from document_to_anki.core.flashcard_generator import FlashcardGenerator

# Custom LLM client with specific settings
llm_client = LLMClient(
    model="gemini/gemini-pro",
    max_tokens=6000  # Larger chunks for complex documents
)

# Use custom client with flashcard generator
flashcard_gen = FlashcardGenerator(llm_client=llm_client)

# Process text directly
text = """
Photosynthesis is the process by which plants convert light energy into chemical energy.
It occurs in the chloroplasts and involves two main stages: light reactions and the Calvin cycle.
The overall equation is: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2
"""

# Generate flashcards directly from text
flashcard_data = llm_client.generate_flashcards_from_text_sync(text)

# Create flashcard objects
flashcards = []
for data in flashcard_data:
    flashcard = Flashcard.create(
        question=data["question"],
        answer=data["answer"],
        card_type=data["card_type"],
        source_file="biology_notes.txt"
    )
    flashcards.append(flashcard)

print(f"Generated {len(flashcards)} flashcards from text")
```

### Error Handling and Validation

```python
from document_to_anki.core.document_processor import DocumentProcessingError
from document_to_anki.core.flashcard_generator import FlashcardGenerationError
from document_to_anki.models.flashcard import Flashcard
from pathlib import Path

def safe_document_processing(file_path: str):
    """Example of robust document processing with error handling."""
    
    try:
        # Initialize processor
        doc_processor = DocumentProcessor()
        
        # Validate file first
        path = Path(file_path)
        if not doc_processor.validate_upload_path(path):
            print(f"❌ Invalid file: {file_path}")
            return None
            
        # Process document
        result = doc_processor.process_upload(path)
        
        if not result.success:
            print("❌ Document processing failed:")
            for error in result.errors:
                print(f"  • {error}")
            return None
            
        if result.warnings:
            print("⚠️ Warnings:")
            for warning in result.warnings:
                print(f"  • {warning}")
        
        print(f"✅ Successfully processed {result.file_count} files")
        return result
        
    except DocumentProcessingError as e:
        print(f"❌ Document processing error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def safe_flashcard_generation(text_content: list[str], source_files: list[str]):
    """Example of robust flashcard generation with error handling."""
    
    try:
        # Initialize generator
        flashcard_gen = FlashcardGenerator()
        
        # Generate flashcards
        result = flashcard_gen.generate_flashcards(text_content, source_files)
        
        if not result.success:
            print("❌ Flashcard generation failed:")
            for error in result.errors:
                print(f"  • {error}")
            return None
            
        if result.warnings:
            print("⚠️ Warnings:")
            for warning in result.warnings:
                print(f"  • {warning}")
        
        print(f"✅ Generated {result.flashcard_count} flashcards")
        return result
        
    except FlashcardGenerationError as e:
        print(f"❌ Flashcard generation error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

# Usage example
if __name__ == "__main__":
    # Process document safely
    doc_result = safe_document_processing("study-material.pdf")
    
    if doc_result:
        # Generate flashcards safely
        flashcard_result = safe_flashcard_generation(
            [doc_result.text_content],
            doc_result.source_files
        )
        
        if flashcard_result:
            print("🎉 Processing completed successfully!")
```

## Batch Processing

### Processing Multiple Documents

```bash
# Create a script for batch processing
cat > batch_process.sh << 'EOF'
#!/bin/bash

# Process all PDFs in a directory
for pdf in documents/*.pdf; do
    echo "Processing: $pdf"
    document-to-anki "$pdf" --no-preview --batch --output "flashcards/$(basename "$pdf" .pdf)_cards.csv"
done

echo "Batch processing complete!"
EOF

chmod +x batch_process.sh
./batch_process.sh
```

### Python Batch Processing Script

```python
#!/usr/bin/env python3
"""
Batch processing script for multiple documents.
"""

import sys
from pathlib import Path
from document_to_anki.core.document_processor import DocumentProcessor
from document_to_anki.core.flashcard_generator import FlashcardGenerator

def batch_process_directory(input_dir: Path, output_dir: Path):
    """Process all supported files in a directory."""
    
    # Initialize components
    doc_processor = DocumentProcessor()
    flashcard_gen = FlashcardGenerator()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all supported files
    supported_extensions = doc_processor.get_supported_formats()
    files_to_process = []
    
    for ext in supported_extensions:
        files_to_process.extend(input_dir.glob(f"**/*{ext}"))
    
    print(f"Found {len(files_to_process)} files to process")
    
    successful = 0
    failed = 0
    
    for file_path in files_to_process:
        try:
            print(f"\nProcessing: {file_path.name}")
            
            # Process document
            doc_result = doc_processor.process_upload(file_path)
            
            if not doc_result.success:
                print(f"❌ Failed to process {file_path.name}")
                failed += 1
                continue
            
            # Generate flashcards
            flashcard_result = flashcard_gen.generate_flashcards(
                [doc_result.text_content],
                doc_result.source_files
            )
            
            if not flashcard_result.success:
                print(f"❌ Failed to generate flashcards for {file_path.name}")
                failed += 1
                continue
            
            # Export to CSV
            output_file = output_dir / f"{file_path.stem}_flashcards.csv"
            success, summary = flashcard_gen.export_to_csv(output_file)
            
            if success:
                print(f"✅ Generated {summary['exported_flashcards']} flashcards")
                successful += 1
            else:
                print(f"❌ Failed to export flashcards for {file_path.name}")
                failed += 1
                
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            failed += 1
    
    print(f"\n🎉 Batch processing complete!")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python batch_process.py <input_directory> <output_directory>")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    if not input_dir.exists():
        print(f"❌ Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    batch_process_directory(input_dir, output_dir)
```

## Configuration Examples

### Environment Configuration

```bash
# .env file example
GEMINI_API_KEY=your-gemini-api-key-here
LOG_LEVEL=INFO
LITELLM_TIMEOUT=300
MODEL=gemini/gemini-pro

# Optional: Web server configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000

# Optional: Advanced LLM settings
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_TOKENS=20000
```

### Custom Configuration Script

```python
#!/usr/bin/env python3
"""
Configuration management script.
"""

import os
from pathlib import Path

def setup_environment():
    """Set up environment variables for the application."""
    
    # Check if .env file exists
    env_file = Path(".env")
    
    if not env_file.exists():
        print("Creating .env file...")
        
        # Get API key from user
        api_key = input("Enter your Gemini API key: ").strip()
        
        if not api_key:
            print("❌ API key is required!")
            return False
        
        # Create .env file
        env_content = f"""# Document to Anki CLI Configuration

# Required: Gemini API Configuration
GEMINI_API_KEY={api_key}

# Optional: Logging Configuration
LOG_LEVEL=INFO
LOGURU_LEVEL=INFO

# Optional: LLM Configuration
MODEL=gemini/gemini-pro
LITELLM_TIMEOUT=300

# Optional: Web Interface Configuration
WEB_HOST=127.0.0.1
WEB_PORT=8000
"""
        
        env_file.write_text(env_content)
        print("✅ .env file created successfully!")
        
    else:
        print("✅ .env file already exists")
    
    # Validate configuration
    return validate_configuration()

def validate_configuration():
    """Validate the current configuration."""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required variables
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print("✅ Configuration validation passed")
    return True

def test_api_connection():
    """Test connection to the Gemini API."""
    
    try:
        from document_to_anki.core.llm_client import LLMClient
        
        print("Testing API connection...")
        client = LLMClient()
        
        # Test with minimal text
        result = client.generate_flashcards_from_text_sync("Test content for API validation.")
        
        if result:
            print("✅ API connection successful!")
            print(f"Generated {len(result)} test flashcards")
            return True
        else:
            print("❌ API connection failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Document to Anki CLI Configuration Setup")
    print("=" * 50)
    
    # Setup environment
    if setup_environment():
        # Test API connection
        test_api_connection()
    
    print("\n🎉 Setup complete!")
    print("You can now use: document-to-anki your-file.pdf")
```

## Integration Examples

### GitHub Actions Workflow

```yaml
# .github/workflows/generate-flashcards.yml
name: Generate Flashcards

on:
  push:
    paths:
      - 'documents/**'
  workflow_dispatch:

jobs:
  generate-flashcards:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Install dependencies
      run: |
        source $HOME/.cargo/env
        uv sync
    
    - name: Generate flashcards
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        source $HOME/.cargo/env
        source .venv/bin/activate
        
        # Process all documents
        for doc in documents/*.pdf documents/*.docx; do
          if [ -f "$doc" ]; then
            echo "Processing: $doc"
            document-to-anki "$doc" --no-preview --batch --output "flashcards/$(basename "$doc" | cut -d. -f1)_cards.csv"
          fi
        done
    
    - name: Upload flashcards
      uses: actions/upload-artifact@v3
      with:
        name: generated-flashcards
        path: flashcards/
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Expose web interface port
EXPOSE 8000

# Default command
CMD ["uv", "run", "uvicorn", "document_to_anki.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  document-to-anki:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./documents:/app/documents
      - ./output:/app/output
    restart: unless-stopped
```

### Jupyter Notebook Integration

```python
# notebook_example.ipynb
"""
Document to Anki CLI in Jupyter Notebook
"""

# Install in notebook (if needed)
# !pip install -e .

import os
from pathlib import Path
from document_to_anki.core.document_processor import DocumentProcessor
from document_to_anki.core.flashcard_generator import FlashcardGenerator

# Set up API key (use environment variable in production)
os.environ['GEMINI_API_KEY'] = 'your-api-key-here'

# Initialize components
doc_processor = DocumentProcessor()
flashcard_gen = FlashcardGenerator()

# Process a document
file_path = "research-paper.pdf"
result = doc_processor.process_upload(file_path)

print(f"📄 Processed: {result.file_count} files")
print(f"📝 Extracted: {result.total_characters:,} characters")

# Generate flashcards
flashcard_result = flashcard_gen.generate_flashcards(
    [result.text_content],
    result.source_files
)

print(f"🎯 Generated: {flashcard_result.flashcard_count} flashcards")
print(f"⏱️ Time: {flashcard_result.processing_time:.2f} seconds")

# Preview flashcards in notebook
preview_text = flashcard_gen.get_flashcard_preview_text()
print("\n" + "="*50)
print("FLASHCARD PREVIEW")
print("="*50)
print(preview_text[:2000] + "..." if len(preview_text) > 2000 else preview_text)

# Export to CSV
output_path = Path("notebook_flashcards.csv")
success, summary = flashcard_gen.export_to_csv(output_path)

if success:
    print(f"\n✅ Exported {summary['exported_flashcards']} flashcards to {output_path}")
    
    # Display export statistics
    print(f"📊 Q&A cards: {summary['qa_cards']}")
    print(f"📊 Cloze cards: {summary['cloze_cards']}")
    print(f"📊 File size: {summary['file_size_bytes']:,} bytes")
```

These examples demonstrate the flexibility and power of Document to Anki CLI across different use cases and environments. Choose the approach that best fits your workflow and requirements.