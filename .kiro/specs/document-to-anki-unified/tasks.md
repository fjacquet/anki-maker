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

## Unified Configuration Management

- [x] 6. Implement unified Settings class with model and language configuration
  - Create comprehensive Settings class in config.py with model and cardlang fields
  - Implement ModelConfig utility class for model validation and API key checking
  - Implement LanguageConfig utility class for language validation and normalization
  - Add field validators for both model and language configuration using Pydantic v2
  - Create comprehensive error handling for configuration validation failures
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.3, 11.4, 11.5, 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 7. Update .env.example with comprehensive configuration documentation
  - Add MODEL variable documentation with all supported models and required API keys
  - Add CARDLANG variable documentation with all supported languages and formats
  - Include clear examples and usage guidance for both configuration options
  - Document default behavior when variables are not set
  - _Requirements: 13.5, 19.1, 19.4_

## Enhanced LLM Integration

- [x] 8. Implement multi-language, multi-model LLM client
  - Create enhanced LLMClient class supporting configurable models and languages
  - Implement language-specific prompt templates for English, French, Italian, and German
  - Integrate ModelConfig for dynamic model selection and API key validation
  - Implement language validation and retry logic for incorrect language output
  - Add comprehensive error handling for both model and language configuration issues
  - _Requirements: 1.4, 1.5, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 12.1, 12.2, 12.3, 12.4, 12.5, 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 9. Implement enhanced flashcard generation with language support
  - Update FlashcardGenerator class to use unified Settings for model and language configuration
  - Implement language-aware flashcard generation using configured language prompts
  - Add language validation for generated flashcards with retry mechanism
  - Integrate with enhanced LLMClient for multi-language, multi-model support
  - Add comprehensive logging for language and model configuration usage
  - _Requirements: 1.4, 1.5, 1.6, 5.3, 12.5, 14.1, 14.2, 14.3, 14.4, 14.5_

## Flashcard Management

- [x] 10. Implement flashcard preview and editing functionality
  - Implement preview_flashcards() method with rich formatting for CLI display
  - Implement edit_flashcard() method to modify question and answer content
  - Implement delete_flashcard() method to remove unwanted flashcards
  - Implement add_flashcard() method for manual flashcard creation
  - Add validation for all editing operations
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 11. Implement CSV export functionality
  - Implement export_to_csv() method using pandas for efficient data handling
  - Create Anki-compatible CSV format with proper field mapping
  - Add support for both question-answer and cloze deletion card formats
  - Implement file path handling and error checking for export operations
  - Add summary reporting of exported flashcards
  - _Requirements: 1.6, 4.3, 5.1_

## CLI Interface

- [x] 12. Implement enhanced CLI with configuration support
  - Create CLI main.py using Click framework with model and language configuration options
  - Implement file/folder/zip upload arguments and options
  - Add verbose logging option using loguru
  - Implement progress indicators using rich components
  - Add model and language validation on startup with clear error messages
  - Add help text showing supported models and languages
  - _Requirements: 2.6, 4.1, 4.4, 7.3, 10.4, 10.5, 11.4, 19.2, 19.3_

- [x] 13. Implement CLI workflow integration
  - Integrate DocumentProcessor, FlashcardGenerator, and export functionality
  - Implement interactive flashcard review and editing in CLI
  - Add rich-formatted output for flashcard preview
  - Implement confirmation prompts for editing and export operations
  - Add comprehensive error handling with actionable error messages for configuration issues
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.2, 4.5, 7.5_

## Web Interface

- [x] 14. Implement enhanced FastAPI web application
  - Create FastAPI app.py with file upload endpoints and configuration status
  - Implement drag-and-drop file upload functionality using multipart forms
  - Add progress tracking endpoints for long-running operations
  - Implement flashcard preview and editing API endpoints
  - Add CSV export endpoint with proper file download handling
  - Add model and language configuration status endpoints
  - _Requirements: 7.1, 7.2, 7.4, 7.5, 21.1, 21.2, 21.3, 21.4, 21.5_

- [x] 15. Implement web frontend with configuration awareness
  - Create HTML templates using Jinja2 with responsive design
  - Implement drag-and-drop file upload interface with visual feedback
  - Create flashcard preview and editing interface with AJAX functionality
  - Add progress indicators and real-time status updates
  - Implement professional, accessible design following WCAG 2.1 AA standards
  - Display current model and language configuration in web interface
  - _Requirements: 7.1, 7.2, 8.1, 8.2, 8.3, 8.4, 8.5, 21.2_

- [x] 16. Implement web application integration
  - Integrate all core functionality with unified configuration system
  - Add asynchronous processing for file uploads and flashcard generation
  - Implement session management for flashcard editing workflows
  - Add comprehensive error handling with user-friendly error pages
  - Implement proper CORS configuration and security headers
  - _Requirements: 7.4, 7.5_

## Testing and Quality Assurance with pytest-mock

- [x] 17. Review and standardize all mocking to use pytest-mock
  - Audit all existing test files to identify usage of unittest.mock
  - Replace all unittest.mock imports and usage with pytest-mock equivalents
  - Update all test methods to use mocker fixture instead of unittest.mock.patch
  - Ensure all LLM API mocking uses pytest-mock's mocker.patch for litellm calls
  - Standardize environment variable mocking using mocker.patch.dict
  - Update all file system and external dependency mocking to use pytest-mock
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 18. Implement comprehensive unit tests with pytest-mock
  - Create test_models.py with comprehensive Flashcard and ProcessingResult tests
  - Create test_document_processor.py with mocked file operations using pytest-mock
  - Create test_flashcard_generator.py with mocked LLM responses using pytest-mock
  - Create test_llm_client.py with mocked API calls using pytest-mock mocker fixture
  - Create test_unified_config.py with environment variable mocking using pytest-mock
  - Achieve minimum 80% code coverage for all core components
  - _Requirements: 6.1, 6.2, 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 19. Implement integration tests with pytest-mock
  - Create test_cli_integration.py for end-to-end CLI workflow testing with mocked dependencies
  - Create test_web_integration.py for FastAPI endpoint testing with mocked services
  - Create test_end_to_end.py for complete document-to-CSV workflow with mocked LLM calls
  - Add test fixtures with sample documents and expected outputs
  - Test error conditions and edge cases using pytest-mock for external dependencies
  - _Requirements: 6.1, 6.2, 17.1, 17.2, 17.3_

## Language Configuration Testing

- [x] 20. Implement comprehensive language configuration tests
  - Create test_language_config.py with unit tests for all supported language codes
  - Create tests for invalid language codes and error handling behavior
  - Implement integration tests for environment variable parsing and defaults
  - Add end-to-end tests verifying flashcard generation in each supported language using pytest-mock
  - Create performance tests to ensure language processing doesn't impact performance
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 21. Implement language-specific LLM integration tests
  - Create tests that verify prompts are correctly modified for each language using pytest-mock
  - Test language validation and retry logic with mocked LLM responses
  - Add tests for language validation failures and fallback behavior
  - Test cloze deletion card generation for each supported language
  - Verify language consistency across CLI and web interfaces
  - _Requirements: 18.3, 14.4, 14.5_

## Code Quality and Final Polish

- [x] 22. Fix code quality issues and ensure standards compliance
  - Fix ruff linting errors (import sorting, deprecated typing imports, unused imports)
  - Resolve mypy type checking errors (pydantic-settings Field usage, type annotations)
  - Fix failing tests and ensure all tests pass consistently with pytest-mock
  - Ensure code coverage remains above 80% threshold
  - _Requirements: 6.3, 6.4, 6.5_

- [x] 23. Security and dependency validation
  - Run bandit security scanning and address any security issues
  - Run safety dependency vulnerability checking and update vulnerable packages
  - Validate all environment variable handling for security best practices
  - Ensure proper input sanitization and validation throughout the application
  - _Requirements: 6.3, 6.4_

## Documentation and Deployment

- [x] 24. Create comprehensive documentation with configuration examples
  - Update README.md with installation, usage, and API documentation
  - Add docstrings to all public methods and classes
  - Create usage examples for both CLI and web interfaces with model and language configuration
  - Document all configuration options and environment variables (MODEL, CARDLANG, API keys)
  - Add troubleshooting guide for common configuration issues
  - Create migration guide for users upgrading from previous versions
  - _Requirements: 6.5, 19.1, 19.4, 19.5, 20.5_

- [x] 25. Finalize project configuration
  - Update pyproject.toml with proper entry points for CLI and web interfaces
  - Add missing dependencies (PyPDF2, python-docx, Jinja2, python-multipart)
  - Configure development scripts for testing, linting, and running the application
  - Add environment variable configuration for API keys, MODEL, and CARDLANG settings
  - Create sample configuration files and usage examples with comprehensive configuration
  - Document all supported models, languages, and required API keys
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_

## CI/CD and Build System Alignment

- [x] 26. Audit and enhance Makefile for CI compatibility
  - Review all existing Makefile targets to ensure they work in CI environment
  - Test that `uv run` commands work properly in GitHub Actions
  - Verify that all targets handle environment variables correctly
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 27. Update CI workflow for Makefile consistency
  - Replace `uv pip install -e ".[dev]"` with `make install-dev` in all CI jobs
  - Replace custom pytest commands with `make ci-test` in test jobs
  - Replace individual quality check commands with `make quality`
  - Replace `python scripts/validate_config.py` with `make validate`
  - Replace direct `uv build` command with `make build`
  - _Requirements: 16.1, 16.2, 16.3_

- [x] 28. Test and validate CI-Makefile alignment
  - Create test branch with updated CI workflow
  - Run full CI pipeline to ensure all jobs work with Makefile targets
  - Compare CI results with local `make` command results for consistency
  - Verify error handling and exit codes work correctly
  - Update documentation to reflect CI-Makefile alignment
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

## Backward Compatibility and Migration

- [x] 29. Ensure backward compatibility with existing configurations
  - Maintain default behavior when CARDLANG is not set (default to English)
  - Ensure existing .env files continue to work without requiring CARDLANG
  - Preserve all existing MODEL configuration functionality
  - Test upgrade scenarios from previous versions
  - Provide clear migration guidance for configuration changes
  - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

- [x] 30. Update help text and error messages for unified configuration
  - Add comprehensive help text showing both model and language options
  - Provide clear error messages for invalid model or language configurations
  - Include examples of proper configuration in error messages
  - Add guidance for setting up API keys for different models
  - Document the relationship between models and required API keys
  - _Requirements: 19.2, 19.3, 11.4_