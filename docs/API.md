# API Documentation

This document provides comprehensive API documentation for Document to Anki CLI.

## Table of Contents

- [Python API](#python-api)
- [REST API](#rest-api)
- [CLI API](#cli-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Python API

### Core Classes

#### DocumentProcessor

Handles document upload, validation, and text extraction.

```python
from document_to_anki.core.document_processor import DocumentProcessor

processor = DocumentProcessor()
```

**Methods:**

##### `process_upload(upload_path, progress=None, task_id=None)`

Process uploaded content (single file, folder, or ZIP archive).

**Parameters:**
- `upload_path` (str | Path): Path to file, folder, or ZIP archive
- `progress` (Progress, optional): Rich progress instance for tracking
- `task_id` (TaskID, optional): Task ID for progress updates

**Returns:**
- `DocumentProcessingResult`: Contains extracted text and metadata

**Raises:**
- `DocumentProcessingError`: If processing fails

**Example:**
```python
result = processor.process_upload("document.pdf")
print(f"Extracted {result.total_characters} characters")

# For PDFs with processing issues, check warnings
if result.warnings:
    print("Processing warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
        
# Example output for a partially corrupted PDF:
# Extracted 15,432 characters
# Processing warnings:
#   - Skipping malformed page 3 in document.pdf: NullObject error
#   - Skipping malformed page 8 in document.pdf: AttributeError
```

##### `validate_upload_path(upload_path)`

Validate if an upload path is acceptable for processing.

**Parameters:**
- `upload_path` (str | Path): Path to validate

**Returns:**
- `bool`: True if path can be processed

**Example:**
```python
if processor.validate_upload_path("document.pdf"):
    print("File is valid for processing")
```

##### `get_supported_formats()`

Get the set of supported file formats.

**Returns:**
- `set[str]`: Set of supported file extensions

**Example:**
```python
formats = processor.get_supported_formats()
print(f"Supported formats: {formats}")
# Output: {'pdf', '.docx', '.txt', '.md'}
```

#### FlashcardGenerator

Manages flashcard creation, editing, and export functionality.

```python
from document_to_anki.core.flashcard_generator import FlashcardGenerator

generator = FlashcardGenerator()
```

**Properties:**

##### `flashcards`

Get the current list of flashcards.

**Returns:**
- `list[Flashcard]`: Copy of current flashcards list

**Methods:**

##### `generate_flashcards(text_content, source_files=None)`

Generate flashcards from text content using LLM.

**Parameters:**
- `text_content` (list[str]): List of text strings to process
- `source_files` (list[str], optional): Source file names

**Returns:**
- `ProcessingResult`: Contains generated flashcards and metadata

**Example:**
```python
result = generator.generate_flashcards(
    ["Educational content here..."],
    ["textbook.pdf"]
)
print(f"Generated {result.flashcard_count} flashcards")
```

##### `preview_flashcards(flashcards=None, console=None)`

Display rich-formatted preview of flashcards for CLI.

**Parameters:**
- `flashcards` (list[Flashcard], optional): Flashcards to preview
- `console` (Console, optional): Rich Console instance

**Example:**
```python
from rich.console import Console
console = Console()
generator.preview_flashcards(console=console)
```

##### `edit_flashcard(flashcard_id, question, answer)`

Edit an existing flashcard.

**Parameters:**
- `flashcard_id` (str): ID of flashcard to edit
- `question` (str): New question text
- `answer` (str): New answer text

**Returns:**
- `tuple[bool, str]`: (success, message)

**Example:**
```python
success, message = generator.edit_flashcard(
    "abc123",
    "What is the capital of France?",
    "Paris, the largest city in France"
)
```

##### `delete_flashcard(flashcard_id)`

Delete a flashcard by ID.

**Parameters:**
- `flashcard_id` (str): ID of flashcard to delete

**Returns:**
- `tuple[bool, str]`: (success, message)

##### `add_flashcard(question, answer, card_type, source_file=None)`

Add a new flashcard manually.

**Parameters:**
- `question` (str): Question text
- `answer` (str): Answer text
- `card_type` (str): "qa" or "cloze"
- `source_file` (str, optional): Source file name

**Returns:**
- `tuple[Flashcard | None, str]`: (flashcard, message)

**Example:**
```python
flashcard, message = generator.add_flashcard(
    "What is photosynthesis?",
    "The process by which plants convert light energy to chemical energy",
    "qa",
    "biology.txt"
)
```

##### `export_to_csv(output_path, flashcards=None)`

Export flashcards to Anki-compatible CSV format.

**Parameters:**
- `output_path` (Path): Where to save the CSV file
- `flashcards` (list[Flashcard], optional): Flashcards to export

**Returns:**
- `tuple[bool, dict]`: (success, summary_dict)

**Example:**
```python
from pathlib import Path
success, summary = generator.export_to_csv(Path("flashcards.csv"))
if success:
    print(f"Exported {summary['exported_flashcards']} flashcards")
```

##### `get_statistics()`

Get statistics about current flashcards.

**Returns:**
- `dict`: Statistics including counts by type and validation status

**Example:**
```python
stats = generator.get_statistics()
print(f"Total: {stats['total_count']}, Valid: {stats['valid_count']}")
```

#### LLMClient

Handles communication with Gemini LLM through litellm.

```python
from document_to_anki.core.llm_client import LLMClient

client = LLMClient(model="gemini/gemini-2.5-flash", max_tokens=4000)
```

**Methods:**

##### `generate_flashcards_from_text(text)`

Generate flashcards from text content (async).

**Parameters:**
- `text` (str): Input text to process

**Returns:**
- `list[dict[str, str]]`: List of flashcard data dictionaries

**Example:**
```python
import asyncio

async def generate():
    flashcards = await client.generate_flashcards_from_text("Educational content...")
    return flashcards

flashcards = asyncio.run(generate())
```

##### `generate_flashcards_from_text_sync(text)`

Generate flashcards from text content (synchronous).

**Parameters:**
- `text` (str): Input text to process

**Returns:**
- `list[dict[str, str]]`: List of flashcard data dictionaries

**Example:**
```python
flashcards = client.generate_flashcards_from_text_sync("Educational content...")
for card in flashcards:
    print(f"Q: {card['question']}")
    print(f"A: {card['answer']}")
```

##### `chunk_text_for_processing(text, max_tokens=None)`

Split large text into manageable chunks.

**Parameters:**
- `text` (str): Text to chunk
- `max_tokens` (int, optional): Maximum tokens per chunk

**Returns:**
- `list[str]`: List of text chunks

#### TextExtractor

Handles text extraction from various document formats with enhanced PDF processing.

```python
from document_to_anki.utils.text_extractor import TextExtractor

extractor = TextExtractor()
```

**Methods:**

##### `extract_text(file_path)`

Extract text from a file with enhanced error handling for PDFs.

**Parameters:**
- `file_path` (Path): Path to the file to extract text from

**Returns:**
- `str`: Extracted text content

**Raises:**
- `TextExtractionError`: If extraction fails completely

**Enhanced PDF Features:**
- **Malformed PDF Support**: Uses `strict=False` for lenient parsing
- **Page-by-Page Processing**: Continues processing even if individual pages fail
- **Error Recovery**: Automatically skips corrupted pages and processes remaining content
- **Detailed Logging**: Reports successful vs. failed page processing

**Example:**
```python
from pathlib import Path

# Extract from a potentially problematic PDF
try:
    text = extractor.extract_text(Path("scanned-document.pdf"))
    print(f"Extracted {len(text)} characters")
    
    # Check logs for processing details:
    # INFO: Successfully extracted text from PDF: scanned-document.pdf (18/20 pages processed)
    # This indicates 18 pages were successfully processed, 2 were skipped
    
except TextExtractionError as e:
    print(f"Extraction failed: {e}")
    # This only occurs if NO pages could be processed
```

### Data Models

#### Flashcard

Pydantic model representing a single flashcard.

```python
from document_to_anki.models.flashcard import Flashcard

# Create a new flashcard
flashcard = Flashcard.create(
    question="What is the capital of France?",
    answer="Paris",
    card_type="qa",
    source_file="geography.txt"
)
```

**Fields:**
- `id` (str): Unique identifier (UUID4)
- `question` (str): Question text
- `answer` (str): Answer text
- `card_type` (Literal["qa", "cloze"]): Card type
- `source_file` (str | None): Original file name
- `created_at` (datetime): Creation timestamp

**Methods:**

##### `create(question, answer, card_type, source_file=None)` (classmethod)

Create a new flashcard with auto-generated ID.

##### `to_csv_row()`

Convert flashcard to Anki-compatible CSV format.

**Returns:**
- `list[str]`: CSV row data

##### `validate_content()`

Validate flashcard content.

**Returns:**
- `bool`: True if valid

#### ProcessingResult

Represents the result of document processing or flashcard generation.

**Fields:**
- `flashcards` (list[Flashcard]): Generated flashcards
- `source_files` (list[str]): Source file names
- `processing_time` (float): Time taken in seconds
- `errors` (list[str]): Error messages
- `warnings` (list[str]): Warning messages

**Properties:**
- `success` (bool): True if no errors
- `flashcard_count` (int): Number of flashcards
- `valid_flashcard_count` (int): Number of valid flashcards

**Methods:**

##### `get_summary()`

Get human-readable summary.

**Returns:**
- `str`: Formatted summary text

## REST API

The web interface exposes a comprehensive REST API for programmatic access.

### Interactive API Documentation (Swagger/OpenAPI)

The FastAPI web interface automatically generates interactive API documentation that you can access when the server is running:

#### 📚 **Available Documentation Endpoints**

1. **Swagger UI**: `http://localhost:8000/docs`
   - Interactive API documentation with a modern UI
   - Test endpoints directly from your browser
   - View detailed request/response schemas
   - Try out API calls with sample data

2. **ReDoc**: `http://localhost:8000/redoc`
   - Alternative documentation format
   - Clean, readable API documentation
   - Better for reading and understanding the API structure

3. **OpenAPI JSON Schema**: `http://localhost:8000/openapi.json`
   - Raw OpenAPI 3.0 specification in JSON format
   - Can be imported into API testing tools like Postman, Insomnia
   - Use for code generation in various programming languages

#### 🚀 **How to Access Interactive Documentation**

1. Start the web server:
   ```bash
   document-to-anki-web
   # or
   uvicorn document_to_anki.web.app:app --host 0.0.0.0 --port 8000
   ```

2. Open your browser and navigate to:
   - **Swagger UI**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

#### 🔧 **What You'll Find in the Documentation**

The interactive documentation automatically includes:
- All API endpoints with HTTP methods and paths
- Request/response schemas with examples
- Parameter descriptions and validation rules
- Error response formats
- Model definitions (Pydantic schemas)
- Authentication requirements (currently none)

#### 💡 **Benefits of Interactive Documentation**

- **Always Up-to-Date**: Generated directly from code, so it's never outdated
- **Interactive Testing**: Test API endpoints without writing code
- **Schema Validation**: See exactly what data formats are expected
- **Code Examples**: Auto-generated request examples in multiple formats
- **Error Handling**: Clear documentation of error responses

### Base URL

```
http://localhost:8000/api
```

### Authentication

Currently, no authentication is required. API keys may be added in future versions.

### Content Types

- Request: `application/json` or `multipart/form-data` (for file uploads)
- Response: `application/json`

### Endpoints

#### Upload Files

**POST** `/upload`

Upload files and start processing.

**Request:**
- Content-Type: `multipart/form-data`
- Form fields:
  - `files`: One or more files to upload
  - `session_id` (optional): Existing session ID

**Response:**
```json
{
  "session_id": "uuid-string",
  "status": "processing",
  "progress": 10,
  "message": "Files uploaded successfully",
  "flashcard_count": 0,
  "errors": []
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "files=@document.pdf" \
  -F "files=@notes.txt"
```

#### Get Processing Status

**GET** `/status/{session_id}`

Get current processing status for a session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "status": "completed",
  "progress": 100,
  "message": "Successfully generated 25 flashcards",
  "flashcard_count": 25,
  "errors": []
}
```

#### Get Flashcards

**GET** `/flashcards/{session_id}`

Get all flashcards for a session.

**Response:**
```json
[
  {
    "id": "flashcard-uuid",
    "question": "What is the capital of France?",
    "answer": "Paris",
    "card_type": "qa",
    "source_file": "geography.pdf",
    "created_at": "2024-01-01T12:00:00"
  }
]
```

#### Edit Flashcard

**PUT** `/flashcards/{session_id}/{flashcard_id}`

Edit an existing flashcard.

**Request:**
```json
{
  "question": "What is the capital city of France?",
  "answer": "Paris, the largest city in France"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Flashcard updated successfully"
}
```

#### Delete Flashcard

**DELETE** `/flashcards/{session_id}/{flashcard_id}`

Delete a flashcard.

**Response:**
```json
{
  "success": true,
  "message": "Deleted flashcard: What is the capital..."
}
```

#### Add Flashcard

**POST** `/flashcards/{session_id}`

Add a new flashcard to the session.

**Request:**
```json
{
  "question": "What is photosynthesis?",
  "answer": "The process by which plants convert light energy",
  "card_type": "qa",
  "source_file": "biology.txt"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Added new flashcard",
  "flashcard": {
    "id": "new-flashcard-uuid",
    "question": "What is photosynthesis?",
    "answer": "The process by which plants convert light energy",
    "card_type": "qa",
    "source_file": "biology.txt",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

#### Export Flashcards

**POST** `/export/{session_id}`

Export flashcards as CSV file.

**Request:**
```json
{
  "filename": "my-flashcards.csv"
}
```

**Response:**
- Content-Type: `text/csv`
- File download with specified filename

#### Session Statistics

**GET** `/sessions/{session_id}/statistics`

Get statistics for a session's flashcards.

**Response:**
```json
{
  "total_count": 25,
  "valid_count": 24,
  "invalid_count": 1,
  "qa_count": 20,
  "cloze_count": 5,
  "source_files": ["document.pdf", "notes.txt"]
}
```

#### Validate Flashcards

**POST** `/sessions/{session_id}/validate`

Validate all flashcards in a session.

**Response:**
```json
{
  "valid_flashcards": [...],
  "invalid_flashcards": [...],
  "validation_summary": {
    "total": 25,
    "valid": 24,
    "invalid": 1
  }
}
```

#### Clean Up Session

**DELETE** `/sessions/{session_id}`

Clean up session and temporary files.

**Response:**
```json
{
  "success": true,
  "message": "Session cleaned up successfully"
}
```

#### Health Check

**GET** `/health`

Check API health and status.

**Response:**
```json
{
  "status": "healthy",
  "message": "Document to Anki API is running",
  "active_sessions": 3,
  "supported_formats": [".pdf", ".docx", ".txt", ".md"]
}
```

#### Get Model Configuration

**GET** `/config/model`

Get current model configuration status.

**Response:**
```json
{
  "current_model": "gemini/gemini-2.5-flash",
  "is_valid": true,
  "supported_models": [
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-pro", 
    "openai/gpt-4o",
    "openai/gpt-4",
    "openai/gpt-3.5-turbo",
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    "openai/gpt-4.1-nano",
    "openai/gpt-5",
    "openai/gpt-5-mini",
    "openai/gpt-5-nano"
  ],
  "required_api_key": "GEMINI_API_KEY"
}
```

## CLI API

### Commands

#### `document-to-anki`

Main command for converting documents.

**Usage:**
```bash
document-to-anki [OPTIONS] INPUT_PATH
```

**Arguments:**
- `INPUT_PATH`: File, folder, or ZIP archive to process

**Options:**
- `--output, -o PATH`: Output CSV file path
- `--no-preview`: Skip flashcard preview and editing
- `--batch`: Enable batch processing mode
- `--verbose, -v`: Enable verbose logging
- `--version`: Show version information
- `--help`: Show help message

**Examples:**
```bash
# Basic usage
document-to-anki document.pdf

# Specify output
document-to-anki document.pdf --output flashcards.csv

# Batch mode (no interaction)
document-to-anki document.pdf --no-preview --batch

# Verbose logging
document-to-anki document.pdf --verbose
```

#### `document-to-anki batch-convert`

Batch process multiple documents.

**Usage:**
```bash
document-to-anki batch-convert [OPTIONS] INPUT_PATHS...
```

**Arguments:**
- `INPUT_PATHS`: Multiple files, folders, or ZIP archives

**Options:**
- `--output-dir, -o PATH`: Output directory for CSV files
- `--batch`: Enable batch processing mode

**Example:**
```bash
document-to-anki batch-convert file1.pdf file2.docx folder/ \
  --output-dir ./flashcards/
```

#### `document-to-anki-web`

Start the web interface.

**Usage:**
```bash
document-to-anki-web
```

**Alternative:**
```bash
uvicorn document_to_anki.web.app:app --host 0.0.0.0 --port 8000
```

## Error Handling

### Exception Hierarchy

```
Exception
├── DocumentProcessingError
├── FlashcardGenerationError
├── TextExtractionError
└── FileHandlingError
```

### Error Response Format

**REST API Errors:**
```json
{
  "detail": "Error message",
  "error_code": "PROCESSING_FAILED",
  "suggestions": [
    "Check file format is supported",
    "Verify file is not corrupted"
  ]
}
```

**Python API Errors:**
```python
try:
    result = processor.process_upload("document.pdf")
except DocumentProcessingError as e:
    print(f"Processing failed: {e}")
    # Handle error appropriately
```

### Common Error Codes

- `FILE_NOT_FOUND`: Input file doesn't exist
- `UNSUPPORTED_FORMAT`: File format not supported
- `FILE_TOO_LARGE`: File exceeds size limit
- `PROCESSING_FAILED`: Document processing failed
- `GENERATION_FAILED`: Flashcard generation failed
- `API_ERROR`: LLM API error
- `VALIDATION_ERROR`: Data validation failed
- `EXPORT_ERROR`: CSV export failed

## Testing and Validation

### Integration Tests

The project includes comprehensive integration tests to validate configuration and startup:

#### Model Configuration Test
```bash
# Run the integration test
python test_integration_check.py
```

This test validates:
- FlashcardGenerator properly uses ModelConfig for model selection
- Default model configuration with valid API keys
- Custom model selection with appropriate API keys
- Error handling for invalid models and missing API keys
- ModelConfig method functionality

**Example output:**
```
Testing ModelConfig methods...
✓ Supported models: 11 models
✓ Default model: gemini/gemini-2.5-flash
✓ Model from env: openai/gpt-4
✓ Required API key for Gemini: GEMINI_API_KEY
✓ Required API key for OpenAI: OPENAI_API_KEY
All ModelConfig method tests passed! ✓

Testing FlashcardGenerator ModelConfig integration...
✓ Default model test passed: gemini/gemini-2.5-flash
✓ Custom model test passed: openai/gpt-4
✓ Invalid model test passed: Unsupported model 'invalid/model'
✓ Missing API key test passed: Missing API key for model 'gemini/gemini-2.5-flash'
All FlashcardGenerator ModelConfig integration tests passed! ✓

🎉 All integration tests passed!
```

#### Web App Startup Validation Test
```bash
# Run the startup validation test
python test_startup_validation.py
```

This test validates:
- Web application startup with valid configuration
- Proper error handling for invalid models during startup
- Proper error handling for missing API keys during startup
- FastAPI lifespan event configuration validation
- Configuration error propagation in web interface

**Example output:**
```
Test 1: Valid configuration
✅ Valid configuration startup succeeded

Test 2: Invalid model
✅ Invalid model correctly failed: Unsupported model 'invalid/model'. Supported models: gemini/gemini-2.5-flash, gemini/gemini-2.5-pro, openai/gpt-4o, ...

Test 3: Missing API key
✅ Missing API key correctly failed: Missing API key for model 'gemini/gemini-2.5-flash'. Please set the GEMINI_API_KEY environment variable.

🎉 All startup validation tests passed!
```

## Examples

### Complete Python Workflow

```python
from pathlib import Path
from document_to_anki.core.document_processor import DocumentProcessor
from document_to_anki.core.flashcard_generator import FlashcardGenerator

def process_document_to_flashcards(input_file: str, output_file: str):
    """Complete workflow example."""
    
    # Initialize components
    processor = DocumentProcessor()
    generator = FlashcardGenerator()
    
    try:
        # Step 1: Process document
        print(f"Processing document: {input_file}")
        doc_result = processor.process_upload(input_file)
        
        if not doc_result.success:
            print("Document processing failed:")
            for error in doc_result.errors:
                print(f"  - {error}")
            return False
        
        print(f"Extracted {doc_result.total_characters:,} characters")
        
        # Step 2: Generate flashcards
        print("Generating flashcards...")
        flashcard_result = generator.generate_flashcards(
            [doc_result.text_content],
            doc_result.source_files
        )
        
        if not flashcard_result.success:
            print("Flashcard generation failed:")
            for error in flashcard_result.errors:
                print(f"  - {error}")
            return False
        
        print(f"Generated {flashcard_result.flashcard_count} flashcards")
        
        # Step 3: Export to CSV
        print(f"Exporting to: {output_file}")
        success, summary = generator.export_to_csv(Path(output_file))
        
        if success:
            print(f"Successfully exported {summary['exported_flashcards']} flashcards")
            return True
        else:
            print("Export failed:")
            for error in summary.get('errors', []):
                print(f"  - {error}")
            return False
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

# Usage
if __name__ == "__main__":
    success = process_document_to_flashcards("textbook.pdf", "flashcards.csv")
    if success:
        print("✅ Processing completed successfully!")
    else:
        print("❌ Processing failed!")
```

### REST API Client Example

```python
import requests
import time
from pathlib import Path

class DocumentToAnkiClient:
    """REST API client example."""
    
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.session_id = None
    
    def upload_file(self, file_path: str) -> bool:
        """Upload file and start processing."""
        url = f"{self.base_url}/upload"
        
        with open(file_path, 'rb') as f:
            files = {'files': f}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data['session_id']
            print(f"Upload successful. Session ID: {self.session_id}")
            return True
        else:
            print(f"Upload failed: {response.text}")
            return False
    
    def wait_for_completion(self, timeout: int = 300) -> bool:
        """Wait for processing to complete."""
        if not self.session_id:
            return False
        
        url = f"{self.base_url}/status/{self.session_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                progress = data['progress']
                
                print(f"Status: {status}, Progress: {progress}%")
                
                if status == 'completed':
                    print(f"Processing completed! Generated {data['flashcard_count']} flashcards")
                    return True
                elif status == 'error':
                    print(f"Processing failed: {data['message']}")
                    return False
            
            time.sleep(5)  # Check every 5 seconds
        
        print("Timeout waiting for completion")
        return False
    
    def get_flashcards(self) -> list:
        """Get all flashcards."""
        if not self.session_id:
            return []
        
        url = f"{self.base_url}/flashcards/{self.session_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get flashcards: {response.text}")
            return []
    
    def export_csv(self, filename: str = "flashcards.csv") -> bool:
        """Export flashcards to CSV."""
        if not self.session_id:
            return False
        
        url = f"{self.base_url}/export/{self.session_id}"
        data = {'filename': filename}
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"Exported to {filename}")
            return True
        else:
            print(f"Export failed: {response.text}")
            return False

# Usage example
client = DocumentToAnkiClient()

if client.upload_file("document.pdf"):
    if client.wait_for_completion():
        flashcards = client.get_flashcards()
        print(f"Retrieved {len(flashcards)} flashcards")
        
        client.export_csv("my-flashcards.csv")
```

This comprehensive API documentation covers all aspects of using Document to Anki CLI programmatically, whether through Python, REST API, or CLI interfaces.