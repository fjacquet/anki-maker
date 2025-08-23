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
  - Create ModelConfig class to handle environment variable-based model selection ✅
  - Implement get_model_from_env() to read MODEL environment variable with fallback to "gemini/gemini-2.5-flash" ✅
  - Implement validate_model_config() to check supported models and required API keys ✅
  - Add get_supported_models() method to list available model options ✅
  - Create ConfigurationError exception class for model configuration issues ✅
  - **MISSING**: Integrate ModelConfig into LLMClient and FlashcardGenerator to actually use environment-based model selection
  - **MISSING**: Update CLI and web interfaces to validate model configuration on startup
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

## LLM Integration

- [x] 7. Implement LLM client for configurable model integration
  - Create LLMClient class using litellm supporting multiple model providers ✅
  - Implement generate_flashcards_from_text() with carefully crafted prompts ✅
  - Create prompts that generate both question-answer and cloze deletion cards ✅
  - Implement chunk_text_for_processing() to handle large documents within token limits ✅
  - Add retry logic with exponential backoff for API failures ✅
  - **MISSING**: Integrate ModelConfig for dynamic model selection and validation
  - **MISSING**: Update LLMClient constructor to use ModelConfig.validate_and_get_model()
  - _Requirements: 1.4, 1.5, 5.2, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 8. Implement flashcard generation logic
  - Create FlashcardGenerator class to manage flashcard creation and editing ✅
  - Implement generate_flashcards() method that uses LLMClient to create flashcards from text ✅
  - Add logic to parse LLM responses into Flashcard objects ✅
  - Implement batch processing for multiple text chunks ✅
  - Add validation and error handling for malformed LLM responses ✅
  - Update FlashcardGenerator to use ModelConfig-configured LLMClient ✅
  - _Requirements: 1.4, 1.5, 1.6, 5.3, 10.1, 10.2, 10.3, 10.4, 10.5_

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
  - Create CLI main.py using Click framework for command-line interface ✅
  - Implement file/folder/zip upload arguments and options ✅
  - Add verbose logging option using loguru ✅
  - Implement progress indicators using rich components ✅
  - Add batch processing capabilities for multiple files ✅
  - **MISSING**: Integrate ModelConfig for model validation and error handling on startup
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
  - Create FastAPI app.py with file upload endpoints ✅
  - Implement drag-and-drop file upload functionality using multipart forms ✅
  - Add progress tracking endpoints for long-running operations ✅
  - Implement flashcard preview and editing API endpoints ✅
  - Add CSV export endpoint with proper file download handling ✅
  - **MISSING**: Add model configuration status endpoint for environment validation
  - **MISSING**: Integrate ModelConfig validation in web app startup
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
  - ✅ **ADDED**: Created `test_integration_check.py` for comprehensive ModelConfig integration validation
  - ✅ **ADDED**: Created `test_startup_validation.py` for web app startup configuration validation
  - _Requirements: 6.1, 6.2_

## Model Configuration Integration

- [x] 18. Integrate ModelConfig throughout the application
  - Update LLMClient constructor to use ModelConfig.validate_and_get_model() instead of hardcoded model
  - Update FlashcardGenerator to pass configured model to LLMClient
  - Add model validation to CLI startup with clear error messages for invalid models or missing API keys
  - Add model configuration status endpoint to web interface (/api/config/model)
  - Add model validation to web app startup with proper error handling
  - Update all tests to mock ModelConfig appropriately
  - ✅ **COMPLETED**: Created comprehensive integration test (`test_integration_check.py`) to validate FlashcardGenerator ModelConfig integration
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

## Code Quality and Final Polish

- [x] 19. Fix code quality issues and ensure standards compliance
  - Fix ruff linting errors (import sorting, deprecated typing imports, unused imports)
  - Resolve mypy type checking errors (pydantic-settings Field usage, type annotations)
  - Fix failing tests and ensure all 199 tests pass consistently
  - Ensure code coverage remains above 80% threshold
  - _Requirements: 6.3, 6.4, 6.5_

- [x] 20. Security and dependency validation
  - Run bandit security scanning and address any security issues
  - Run safety dependency vulnerability checking and update vulnerable packages
  - Validate all environment variable handling for security best practices
  - Ensure proper input sanitization and validation throughout the application
  - _Requirements: 6.3, 6.4_

## Documentation and Deployment

- [x] 21. Create comprehensive documentation
  - Update README.md with installation, usage, and API documentation
  - Add docstrings to all public methods and classes
  - Create usage examples for both CLI and web interfaces
  - Document configuration options and environment variables
  - Add troubleshooting guide for common issues
  - _Requirements: 6.5_

- [x] 22. Finalize project configuration
  - Update pyproject.toml with proper entry points for CLI and web interfaces
  - Add missing dependencies (PyPDF2, python-docx, Jinja2, python-multipart)
  - Configure development scripts for testing, linting, and running the application
  - Add environment variable configuration for API keys and MODEL settings
  - Create sample configuration files and usage examples with model configuration
  - Document supported models and required API keys
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 10.1, 10.2, 10.3, 10.4, 10.5_
#
# CI/CD and Build System Alignment

- [x] 23. Audit and enhance Makefile for CI compatibility
  - Review all existing Makefile targets to ensure they work in CI environment
  - Test that `uv run` commands work properly in GitHub Actions
  - Verify that all targets handle environment variables correctly
  - _Requirements: CI alignment for consistent local/CI development_

- [x] 24. Add missing CI-specific Makefile targets
  - Create `ci-setup` target that combines installation and basic validation
  - Ensure `ci-test` target exists and is optimized for CI (fail-fast, concise output)
  - Ensure `ci-quality` target exists and runs all quality checks efficiently
  - Add proper error handling and exit codes to all CI targets
  - _Requirements: CI optimization and consistency_

- [x] 25. Update CI workflow dependency installation
  - Replace `uv pip install -e ".[dev]"` with `make install-dev` in all CI jobs
  - Ensure `make install-dev` works correctly in GitHub Actions environment
  - Test that dependency installation is consistent between local and CI
  - _Requirements: Dependency management consistency_

- [x] 26. Update CI workflow test execution
  - Replace custom pytest commands with `make ci-test` in test job
  - Replace coverage commands with `make test-cov` where appropriate
  - Ensure test results and coverage reports are generated correctly
  - Verify that test failures propagate properly through Makefile
  - _Requirements: Test execution consistency_

- [x] 27. Update CI workflow quality checks
  - Replace individual ruff, mypy, bandit commands with `make ci-quality`
  - Ensure all quality check outputs are preserved for CI reporting
  - Test that quality check failures fail the CI job appropriately
  - _Requirements: Quality assurance consistency_

- [x] 28. Update CI workflow validation steps
  - Replace `python scripts/validate_config.py` with `make validate`
  - Ensure configuration validation works with CI environment variables
  - Test that validation failures are properly reported
  - _Requirements: Configuration validation consistency_

- [x] 29. Update CI workflow build process
  - Replace direct `uv build` command with `make build`
  - Ensure build artifacts are created correctly through Makefile
  - Test that build process works identically to direct commands
  - _Requirements: Build process consistency_

- [x] 30. Update integration test job
  - Replace custom integration test commands with `make test-integration`
  - Ensure integration tests run properly through Makefile
  - Verify that integration test results are reported correctly
  - _Requirements: Integration testing consistency_

- [x] 31. Handle scripts directory alignment
  - Document the relationship between scripts and Makefile targets
  - Decide whether to integrate `scripts/quality_check.sh` into Makefile or remove it
  - Update any remaining script calls in CI to use Makefile targets instead
  - _Requirements: Script and Makefile consistency_

- [x] 32. Test and validate CI-Makefile alignment
  - Create test branch with updated CI workflow
  - Run full CI pipeline to ensure all jobs work with Makefile targets
  - Compare CI results with local `make` command results for consistency
  - Verify error handling and exit codes work correctly
  - _Requirements: End-to-end CI validation_

- [x] 33. Update documentation and cleanup
  - Update README.md to reflect CI-Makefile alignment
  - Document which Makefile targets are used in CI
  - Remove or update any outdated references to direct commands in CI
  - Add troubleshooting guide for CI-Makefile issues
  - _Requirements: Documentation and maintenance_

## French Language Support Implementation

- [ ] 34. Implement French language prompt engineering
  - Create French-specific prompt templates in LLMClient for flashcard generation
  - Update generate_flashcards_from_text() to use French prompts that explicitly instruct the LLM to generate French flashcards
  - Implement get_french_prompt_template() method with carefully crafted French instructions
  - Add prompt variations for different content types (academic, technical, general)
  - Test prompts with various input languages to ensure French output
  - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [ ] 35. Implement French language validation system
  - Create FrenchLanguageValidator class with linguistic pattern detection
  - Implement validate_french_content() method using regex patterns for French linguistic markers
  - Implement validate_flashcard_french() method to check both questions and answers
  - Add French grammar and vocabulary validation logic
  - Create comprehensive test cases for French language detection
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 36. Implement French output regeneration mechanism
  - Add validate_french_output() method to LLMClient for post-generation validation
  - Implement regenerate_non_french_content() method with enhanced French prompts
  - Add request_regeneration_if_needed() logic in FlashcardGenerator
  - Implement retry logic with progressively stronger French emphasis
  - Add logging and error handling for repeated regeneration failures
  - _Requirements: 17.1, 17.2, 17.5_

- [ ] 37. Update flashcard generation workflow for French
  - Modify FlashcardGenerator.generate_flashcards() to include French language validation
  - Implement validate_language_quality() method to check all generated flashcards
  - Add regenerate_non_french_flashcards() method for batch regeneration
  - Update the generation workflow to automatically validate and regenerate non-French content
  - Add progress indicators for language validation and regeneration steps
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 38. Implement French cloze deletion support
  - Create French-specific cloze deletion patterns that respect French grammar rules
  - Implement create_french_cloze_cards() method with proper sentence structure handling
  - Add gender agreement and verb conjugation awareness for cloze cards
  - Test cloze deletion with various French sentence structures
  - Ensure natural French flow in cloze deletion cards
  - _Requirements: 17.3, 17.4_

- [ ] 39. Add French language error handling
  - Create LanguageError exception class for French language processing issues
  - Add specific error messages for French validation failures
  - Implement fallback mechanisms when French output cannot be achieved
  - Add user feedback for language processing issues in both CLI and web interfaces
  - Create troubleshooting guide for French language generation problems
  - _Requirements: 17.5_

- [ ] 40. Update CLI and web interfaces for French language feedback
  - Add French language status indicators in CLI output
  - Implement progress messages for French validation and regeneration in CLI
  - Add French language validation status to web interface
  - Update error messages to include French language processing information
  - Add configuration option to disable French validation if needed (for testing)
  - _Requirements: 17.1, 17.5_

- [ ] 41. Implement comprehensive French language testing
  - Create test_french_language_validation.py with comprehensive French detection tests
  - Add test cases for various input languages (English, Spanish, etc.) with French output validation
  - Create test_french_flashcard_generation.py for end-to-end French generation testing
  - Add integration tests for French regeneration workflow
  - Test edge cases like mixed-language content and technical terminology
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 42. Update documentation for French language support
  - Document French language generation in README.md
  - Add examples of French flashcard output
  - Document the language validation and regeneration process
  - Add troubleshooting guide for French language issues
  - Update API documentation to reflect French language parameters
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_