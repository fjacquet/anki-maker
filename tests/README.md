# Integration Tests

This directory contains comprehensive integration tests for the Document-to-Anki CLI application.

## Test Structure

### Test Files

1. **`test_cli_integration.py`** - CLI interface integration tests
   - Tests the complete CLI workflow from document processing to CSV export
   - Covers command-line argument parsing, error handling, and user interactions
   - Tests both batch and interactive modes

2. **`test_web_integration.py`** - Web API integration tests
   - Tests the FastAPI web application endpoints
   - Covers file upload, processing status, flashcard management, and CSV export
   - Tests error handling and session management

3. **`test_end_to_end.py`** - End-to-end workflow tests
   - Tests the complete document-to-CSV pipeline
   - Covers single files, multiple files, ZIP archives, and folders
   - Tests flashcard editing, validation, and different card types

4. **`conftest.py`** - Shared fixtures and configuration
   - Provides common test fixtures for documents, flashcards, and mock data
   - Configures pytest markers and test collection
   - Includes performance monitoring and error simulation fixtures

### Test Fixtures

#### Sample Documents
- `tests/fixtures/sample_documents/sample.txt` - Python programming content
- `tests/fixtures/sample_documents/sample.md` - Machine learning content
- `tests/fixtures/expected_outputs/expected_flashcards.json` - Expected flashcard outputs

#### Shared Fixtures (conftest.py)
- `temp_directory` - Temporary directory for test files
- `sample_text_file` - Sample text file with Python content
- `sample_markdown_file` - Sample markdown file with data science content
- `sample_flashcards` - Pre-created flashcard objects for testing
- `mock_llm_client` - Mocked LLM client for consistent responses
- `performance_monitor` - Performance monitoring for tests

## Test Categories

### CLI Integration Tests (`test_cli_integration.py`)

#### Basic CLI Functionality
- Help and version commands
- Command-line argument validation
- File type validation and error handling

#### Document Processing Workflow
- Single file processing (TXT, MD, PDF, DOCX)
- Folder processing with multiple files
- ZIP archive processing
- Batch processing of multiple inputs

#### Interactive Features
- Flashcard preview and editing
- Adding and deleting flashcards
- Export confirmation and cancellation

#### Error Handling
- Document processing errors
- Flashcard generation failures
- Permission and file system errors
- Network and API errors

### Web Integration Tests (`test_web_integration.py`)

#### API Endpoints
- Health check endpoint
- File upload with validation
- Processing status tracking
- Flashcard CRUD operations
- CSV export functionality

#### Session Management
- Session creation and cleanup
- Concurrent session handling
- Session data persistence

#### Error Handling
- Invalid file uploads
- Processing failures
- API validation errors
- Export errors

#### Performance Tests
- Large file upload handling
- Concurrent request processing
- Memory usage monitoring

### End-to-End Tests (`test_end_to_end.py`)

#### Complete Workflows
- Single file: document → flashcards → CSV
- Multiple files: folder → consolidated flashcards → CSV
- ZIP archive: extraction → processing → export

#### Flashcard Management
- Editing flashcard content
- Adding custom flashcards
- Deleting unwanted flashcards
- Validation and quality checks

#### Advanced Scenarios
- Large document processing with chunking
- Mixed card types (Q&A and cloze deletion)
- Error recovery and retry logic
- Performance and memory usage testing

## Running Tests

### Run All Integration Tests
```bash
pytest tests/test_cli_integration.py tests/test_web_integration.py tests/test_end_to_end.py -v
```

### Run Specific Test Categories
```bash
# CLI tests only
pytest tests/test_cli_integration.py -v

# Web API tests only
pytest tests/test_web_integration.py -v

# End-to-end tests only
pytest tests/test_end_to_end.py -v
```

### Run Tests with Markers
```bash
# Integration tests only
pytest -m integration -v

# Slow tests (excluded by default)
pytest -m slow -v

# CLI-specific tests
pytest -m cli -v

# Web-specific tests
pytest -m web -v
```

### Run Tests with Coverage
```bash
pytest tests/test_*_integration.py --cov=src/document_to_anki --cov-report=html
```

## Test Configuration

### Pytest Markers
- `integration` - Integration tests
- `slow` - Slow-running tests
- `cli` - CLI-specific tests
- `web` - Web API-specific tests
- `e2e` - End-to-end tests

### Mock Configuration
Tests use extensive mocking to ensure:
- Consistent LLM responses
- Predictable file operations
- Isolated test execution
- Fast test execution

### Performance Monitoring
Tests include performance monitoring to ensure:
- Reasonable execution times
- Memory usage within limits
- Resource cleanup after tests

## Key Features Tested

### Document Processing
- ✅ Text extraction from multiple formats
- ✅ File validation and error handling
- ✅ Folder and ZIP archive processing
- ✅ Large document chunking

### Flashcard Generation
- ✅ LLM integration with mocked responses
- ✅ Multiple card types (Q&A, cloze deletion)
- ✅ Content validation and quality checks
- ✅ Error handling and retry logic

### User Interfaces
- ✅ CLI command-line interface
- ✅ Web API endpoints
- ✅ Interactive flashcard editing
- ✅ Batch processing modes

### Export Functionality
- ✅ Anki-compatible CSV format
- ✅ File handling and permissions
- ✅ Export validation and statistics
- ✅ Error recovery and cleanup

### Error Handling
- ✅ Comprehensive error scenarios
- ✅ User-friendly error messages
- ✅ Graceful degradation
- ✅ Resource cleanup

## Test Coverage

The integration tests provide comprehensive coverage of:
- Complete user workflows
- Error conditions and edge cases
- Performance characteristics
- Cross-component interactions
- Real-world usage scenarios

These tests complement the unit tests by validating that all components work together correctly to deliver the expected user experience.