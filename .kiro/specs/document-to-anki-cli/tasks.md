# Implementation Plan

## Project Setup and Core Structure

- [x] 1. Set up project structure and core interfaces
  - Create directory structure following the design: src/document_to_anki/ with cli/, web/, core/, models/, and utils/ subdirectories
  - Create all __init__.py files for proper Python package structure
  - Set up entry points in pyproject.toml for CLI and web interfaces
  - _Requirements: 2.1, 2.2_

- [x] 2. Implement core data models
  - Create Flashcard Pydantic v2 model with id, question, answer, card_type, source_file, and created_at fields
  - Implement field validators for content validation using @field_validator and @model_validator
  - Implement to_csv_row() method for Anki-compatible CSV export format
  - Implement validate() method for flashcard content validation
  - Create ProcessingResult Pydantic v2 model for handling processing outcomes
  - _Requirements: 1.6, 3.1, 3.2, 3.3, 3.4_

## Document Processing Core

- [x] 3. Implement text extraction utilities
  - Create TextExtractor class with methods for PDF, DOCX, TXT, and MD file processing
  - Implement extract_text_from_pdf() using PyPDF2
  - Implement extract_text_from_docx() using python-docx
  - Implement extract_text_from_txt() and extract_text_from_md() for plain text files
  - Add comprehensive error handling for corrupted or unsupported files
  - _Requirements: 1.1, 1.2, 4.2_

- [x] 4. Implement file handling utilities
  - Create FileHandler class for managing file uploads and validation
  - Implement validate_file_type() to check supported formats (PDF, DOCX, TXT, MD)
  - Implement process_zip_archive() to extract and process ZIP contents
  - Implement process_folder() to handle directory uploads with multiple files
  - Add file size validation and security checks
  - _Requirements: 1.1, 1.3_

- [x] 5. Implement document processor
  - Create DocumentProcessor class as main orchestrator for document handling
  - Implement process_upload() method to handle single files, folders, or ZIP archives
  - Integrate TextExtractor and FileHandler for complete document processing workflow
  - Add progress tracking and logging using loguru
  - Implement text consolidation for multiple files
  - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.4_

## Configuration Management

- [x] 6. Implement model configuration system
  - Create ModelConfig class to handle environment variable-based model selection
  - Implement get_model_from_env() to read MODEL environment variable with fallback to "gemini/gemini-pro"
  - Implement validate_model_config() to check supported models and required API keys
  - Add get_supported_models() method to list available model options
  - Create ConfigurationError exception class for model configuration issues
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

## LLM Integration

- [x] 7. Implement LLM client for configurable model integration
  - Create LLMClient class using litellm supporting multiple model providers
  - Implement generate_flashcards_from_text() with carefully crafted prompts
  - Create prompts that generate both question-answer and cloze deletion cards
  - Implement chunk_text_for_processing() to handle large documents within token limits
  - Add retry logic with exponential backoff for API failures
  - Integrate ModelConfig for dynamic model selection and validation
  - _Requirements: 1.4, 1.5, 5.2, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 8. Implement flashcard generation logic
  - Create FlashcardGenerator class to manage flashcard creation and editing
  - Implement generate_flashcards() method that uses LLMClient to create flashcards from text
  - Add logic to parse LLM responses into Flashcard objects
  - Implement batch processing for multiple text chunks
  - Add validation and error handling for malformed LLM responses
  - _Requirements: 1.4, 1.5, 1.6, 5.3_

## Flashcard Management

- [x] 9. Implement flashcard preview and editing functionality
  - Implement preview_flashcards() method with rich formatting for CLI display
  - Implement edit_flashcard() method to modify question and answer content
  - Implement delete_flashcard() method to remove unwanted flashcards
  - Implement add_flashcard() method for manual flashcard creation
  - Add validation for all editing operations
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 10. Implement CSV export functionality
  - Implement export_to_csv() method using pandas for efficient data handling
  - Create Anki-compatible CSV format with proper field mapping
  - Add support for both question-answer and cloze deletion card formats
  - Implement file path handling and error checking for export operations
  - Add summary reporting of exported flashcards
  - _Requirements: 1.6, 4.3, 5.1_

## CLI Interface

- [x] 11. Implement CLI main entry point
  - Create CLI main.py using Click framework for command-line interface
  - Implement file/folder/zip upload arguments and options
  - Add verbose logging option using loguru
  - Implement progress indicators using rich components
  - Add batch processing capabilities for multiple files
  - Integrate ModelConfig for model validation and error handling
  - _Requirements: 2.6, 4.1, 4.4, 7.3, 10.4, 10.5_

- [x] 12. Implement CLI workflow integration
  - Integrate DocumentProcessor, FlashcardGenerator, and export functionality
  - Implement interactive flashcard review and editing in CLI
  - Add rich-formatted output for flashcard preview
  - Implement confirmation prompts for editing and export operations
  - Add comprehensive error handling with actionable error messages
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.2, 4.5, 7.5_

## Web Interface

- [x] 13. Implement FastAPI web application
  - Create FastAPI app.py with file upload endpoints
  - Implement drag-and-drop file upload functionality using multipart forms
  - Add progress tracking endpoints for long-running operations
  - Implement flashcard preview and editing API endpoints
  - Add CSV export endpoint with proper file download handling
  - Add model configuration status endpoint for environment validation
  - _Requirements: 7.1, 7.2, 7.4, 7.5, 10.4, 10.5_

- [x] 14. Implement web frontend
  - Create HTML templates using Jinja2 with responsive design
  - Implement drag-and-drop file upload interface with visual feedback
  - Create flashcard preview and editing interface with AJAX functionality
  - Add progress indicators and real-time status updates
  - Implement professional, accessible design following WCAG 2.1 AA standards
  - _Requirements: 7.1, 7.2, 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 15. Implement web application integration
  - Integrate all core functionality (DocumentProcessor, FlashcardGenerator) with web endpoints
  - Add asynchronous processing for file uploads and flashcard generation
  - Implement session management for flashcard editing workflows
  - Add comprehensive error handling with user-friendly error pages
  - Implement proper CORS configuration and security headers
  - _Requirements: 7.4, 7.5_

## Testing and Quality Assurance

- [x] 16. Implement unit tests for core components
  - Create test_models.py with comprehensive Flashcard and ProcessingResult tests
  - Create test_document_processor.py with mocked file operations
  - Create test_flashcard_generator.py with mocked LLM responses
  - Create test_llm_client.py with mocked API calls using pytest-mock (avoiding unittest.mock)
  - Create test_model_config.py with environment variable mocking and validation tests
  - Achieve minimum 80% code coverage for all core components
  - _Requirements: 6.1, 6.2, 10.4, 10.5_

- [x] 17. Implement integration tests
  - Create test_cli_integration.py for end-to-end CLI workflow testing
  - Create test_web_integration.py for FastAPI endpoint testing
  - Create test_end_to_end.py for complete document-to-CSV workflow
  - Add test fixtures with sample documents and expected outputs
  - Test error conditions and edge cases
  - _Requirements: 6.1, 6.2_

## Code Quality and Final Polish

- [ ] 18. Fix code quality issues and ensure standards compliance
  - Fix ruff linting errors (import sorting, deprecated typing imports, unused imports)
  - Resolve mypy type checking errors (pydantic-settings Field usage, type annotations)
  - Fix failing tests and ensure all 199 tests pass consistently
  - Ensure code coverage remains above 80% threshold
  - _Requirements: 6.3, 6.4, 6.5_

- [ ] 19. Security and dependency validation
  - Run bandit security scanning and address any security issues
  - Run safety dependency vulnerability checking and update vulnerable packages
  - Validate all environment variable handling for security best practices
  - Ensure proper input sanitization and validation throughout the application
  - _Requirements: 6.3, 6.4_

## Documentation and Deployment

- [x] 20. Create comprehensive documentation
  - Update README.md with installation, usage, and API documentation
  - Add docstrings to all public methods and classes
  - Create usage examples for both CLI and web interfaces
  - Document configuration options and environment variables
  - Add troubleshooting guide for common issues
  - _Requirements: 6.5_

- [x] 21. Finalize project configuration
  - Update pyproject.toml with proper entry points for CLI and web interfaces
  - Add missing dependencies (PyPDF2, python-docx, Jinja2, python-multipart)
  - Configure development scripts for testing, linting, and running the application
  - Add environment variable configuration for API keys and MODEL settings
  - Create sample configuration files and usage examples with model configuration
  - Document supported models and required API keys
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 10.1, 10.2, 10.3, 10.4, 10.5_