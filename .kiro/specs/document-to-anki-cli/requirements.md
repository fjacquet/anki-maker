# Requirements Document

## Introduction

This feature involves creating a modern Python application that converts digital documents into Anki flashcards using Large Language Models (specifically Gemini). The application will support both CLI and web interfaces, allowing users to upload single files, folders, or ZIP archives, preview and edit generated flashcards, and export them as Anki-importable CSV files. The application will leverage modern Python development practices with Python 3.12+, using uv for package management and incorporating best-in-class tools for development, testing, and user experience.

## Requirements

### Requirement 1

**User Story:** As a student or learner, I want to upload various document formats and have them converted into Anki flashcards, so that I can efficiently study the content using spaced repetition.

#### Acceptance Criteria

1. WHEN a user uploads content THEN the system SHALL accept single files (PDF, DOCX, TXT, MD), folders containing multiple files, or ZIP archives
2. WHEN processing uploads THEN the system SHALL extract readable text content from all supported files
3. WHEN multiple files are provided THEN the system SHALL process all files and consolidate flashcards into a single output
4. WHEN text is extracted THEN the system SHALL send the content to Gemini LLM with carefully crafted prompts to generate high-quality flashcard pairs
5. WHEN flashcards are generated THEN the system SHALL create both question-answer pairs and cloze deletion cards
6. WHEN processing completes THEN the system SHALL format output as Anki-importable CSV files

### Requirement 2

**User Story:** As a developer, I want the CLI to follow modern Python best practices, so that the codebase is maintainable, testable, and follows current standards.

#### Acceptance Criteria

1. WHEN setting up the project THEN the system SHALL use uv for package management and dependency resolution
2. WHEN writing code THEN the system SHALL target Python 3.12+ compatibility
3. WHEN formatting code THEN the system SHALL use ruff for linting and formatting
4. WHEN testing THEN the system SHALL use pytest with pytest-mock for comprehensive test coverage
5. WHEN logging THEN the system SHALL use loguru for structured logging
6. WHEN displaying output THEN the system SHALL use rich for enhanced CLI user experience

### Requirement 3

**User Story:** As a user, I want to preview and edit generated flashcards before exporting, so that I can ensure the quality and relevance of my study materials.

#### Acceptance Criteria

1. WHEN flashcards are generated THEN the system SHALL display a consolidated list of all flashcards for review
2. WHEN reviewing flashcards THEN the system SHALL allow users to edit question and answer content
3. WHEN managing flashcards THEN the system SHALL allow users to delete unwanted flashcards
4. WHEN customizing content THEN the system SHALL allow users to manually add new flashcards
5. WHEN satisfied with content THEN the system SHALL provide an export function to generate the final CSV file

### Requirement 4

**User Story:** As a user, I want clear feedback during document processing, so that I understand the progress and can troubleshoot any issues.

#### Acceptance Criteria

1. WHEN processing starts THEN the system SHALL display a progress indicator using rich components
2. WHEN errors occur THEN the system SHALL provide clear, actionable error messages
3. WHEN processing completes THEN the system SHALL display a summary of generated flashcards
4. WHEN verbose mode is enabled THEN the system SHALL log detailed processing steps using loguru
5. WHEN the process fails THEN the system SHALL log error details and suggest potential solutions

### Requirement 5

**User Story:** As a data analyst, I want the application to handle document analysis efficiently, so that large documents can be processed without performance issues.

#### Acceptance Criteria

1. WHEN processing large documents THEN the system SHALL use numpy and pandas for efficient data manipulation
2. WHEN chunking text THEN the system SHALL split large documents into manageable segments for LLM processing
3. WHEN handling multiple files THEN the system SHALL support batch processing capabilities
4. WHEN memory usage is high THEN the system SHALL implement streaming or chunked processing to manage resources
5. WHEN processing completes THEN the system SHALL clean up temporary files and resources

### Requirement 6

**User Story:** As a quality-conscious developer, I want comprehensive testing and code quality assurance, so that the application is reliable and maintainable.

#### Acceptance Criteria

1. WHEN developing features THEN the system SHALL maintain test coverage above 80%
2. WHEN running tests THEN the system SHALL use pytest with pytest-mock for mocking (avoiding unittest.mock)
3. WHEN checking code quality THEN the system SHALL pass ruff linting without errors
4. WHEN building the package THEN the system SHALL include proper type hints throughout the codebase and use Pydantic v2 for data validation
5. WHEN releasing THEN the system SHALL include comprehensive documentation and usage examples
### Requirement 7

**User Story:** As a user, I want both web and CLI interfaces available, so that I can choose the most convenient way to process my documents.

#### Acceptance Criteria

1. WHEN using the web interface THEN the system SHALL provide drag-and-drop functionality for file uploads
2. WHEN using the web interface THEN the system SHALL display progress indicators during processing
3. WHEN using the CLI THEN the system SHALL accept command-line arguments for batch processing
4. WHEN using either interface THEN the system SHALL provide the same core functionality
5. WHEN errors occur THEN both interfaces SHALL provide clear, actionable error messages

### Requirement 8

**User Story:** As a user, I want the web interface to be professional and accessible, so that I can use it effectively across different devices and abilities.

#### Acceptance Criteria

1. WHEN accessing the web interface THEN the system SHALL display a clean, modern, and professional design
2. WHEN using the interface THEN the system SHALL provide intuitive workflow guidance with clear instructions
3. WHEN interacting with the system THEN the system SHALL provide immediate visual feedback for all user actions
4. WHEN accessing from different devices THEN the system SHALL provide a fully responsive design for desktop, tablet, and mobile
5. WHEN used by people with disabilities THEN the system SHALL meet WCAG 2.1 AA accessibility standards

### Requirement 9

**User Story:** As a developer, I want the system to use Gemini LLM specifically with optimized prompts, so that flashcard generation quality is maximized.

#### Acceptance Criteria

1. WHEN integrating with LLMs THEN the system SHALL use Gemini Pro model through litellm
2. WHEN generating flashcards THEN the system SHALL use carefully crafted prompts to identify key concepts and important facts
3. WHEN creating questions THEN the system SHALL generate clear, concise questions with accurate and relevant answers
4. WHEN producing variety THEN the system SHALL create a mix of question-answer and cloze deletion flashcards
5. WHEN processing content THEN the system SHALL instruct the model to focus on the most important information

### Requirement 10

**User Story:** As a user, I want to configure which LLM model to use via environment variables, so that I can choose the most suitable model for my needs and budget.

#### Acceptance Criteria

1. WHEN starting the application THEN the system SHALL read the MODEL environment variable to determine which LLM model to use
2. WHEN the MODEL variable is set THEN the system SHALL use the specified model (e.g., "gemini/gemini-2.5-flash","gemini/gemini-2.5-pro","openai/gpt-4", 
    "openai/gpt-3.5-turbo", "openai/gpt-4.1", "openai/gpt-4.1-mini", "openai/gpt-4.1-nano", "openai/gpt-5", "openai/gpt-5-mini", "openai/gpt-5-nano", "openai/gpt-4o")
3. WHEN the MODEL variable is not set THEN the system SHALL default to "gemini/gemini-2.5-flash" as the fallback model
4. WHEN an invalid model is specified THEN the system SHALL display a clear error message listing supported models
5. WHEN the model is changed THEN the system SHALL validate that the corresponding API key is available (GEMINI_API_KEY for Gemini models, OPENAI_API_KEY for OpenAI models)
### Requi
rement 11

**User Story:** As a developer, I want the CI pipeline to use the same commands as the Makefile, so that I can be confident that local testing matches CI behavior.

#### Acceptance Criteria

1. WHEN the CI workflow runs quality checks THEN it SHALL use the same `make quality` command that developers use locally
2. WHEN the CI workflow runs tests THEN it SHALL use the same `make test` or `make ci-test` commands available in the Makefile
3. WHEN the CI workflow runs linting THEN it SHALL use the same `make lint` command from the Makefile
4. WHEN the CI workflow runs type checking THEN it SHALL use the same `make type-check` command from the Makefile
5. WHEN the CI workflow runs security checks THEN it SHALL use the same `make security` and `make audit` commands from the Makefile

### Requirement 12

**User Story:** As a developer, I want the CI pipeline to use uv commands consistently, so that dependency management is identical between local and CI environments.

#### Acceptance Criteria

1. WHEN the CI workflow installs dependencies THEN it SHALL use `uv sync` instead of `uv pip install -e ".[dev]"`
2. WHEN the CI workflow runs any command THEN it SHALL use `uv run` prefix consistently as defined in the Makefile
3. WHEN the CI workflow sets up the environment THEN it SHALL follow the same pattern as `make install-dev`

### Requirement 13

**User Story:** As a developer, I want the CI pipeline to have the same build and validation steps as the Makefile, so that the CI process is predictable and debuggable locally.

#### Acceptance Criteria

1. WHEN the CI workflow builds the package THEN it SHALL use `make build` command
2. WHEN the CI workflow validates configuration THEN it SHALL use `make validate` command instead of calling `python scripts/validate_config.py` directly
3. WHEN the CI workflow prepares for release THEN it SHALL use `make prepare-release` command
4. WHEN the CI workflow cleans artifacts THEN it SHALL use `make clean` command when appropriate
5. WHEN the CI workflow installs dependencies THEN it SHALL use `make install-dev` instead of `uv pip install -e ".[dev]"`

### Requirement 14

**User Story:** As a developer, I want the CI pipeline to support the same development workflow targets, so that I can replicate CI steps locally for debugging.

#### Acceptance Criteria

1. WHEN the CI workflow runs pre-commit checks THEN it SHALL use `make pre-commit` command
2. WHEN the CI workflow runs integration tests THEN it SHALL use `make test-integration` command
3. WHEN the CI workflow runs fast tests THEN it SHALL use `make test-fast` or `make ci-test` command
4. WHEN the CI workflow runs coverage tests THEN it SHALL use `make test-cov` command

### Requirement 15

**User Story:** As a maintainer, I want the CI pipeline to be maintainable through the Makefile, so that changes to build logic only need to be made in one place.

#### Acceptance Criteria

1. WHEN a new quality check is added to the Makefile THEN it SHALL automatically be available in CI through make commands
2. WHEN the Makefile commands change THEN the CI workflow SHALL continue to work without modification
3. WHEN debugging CI issues THEN developers SHALL be able to run the exact same commands locally using make
4. IF a Makefile command fails THEN the CI workflow SHALL fail with the same error message and exit code

### Requirement 16

**User Story:** As a developer, I want to understand the relationship between scripts and Makefile targets, so that I know which approach to use for different tasks.

#### Acceptance Criteria

1. WHEN scripts exist in the scripts/ directory THEN they SHALL either be integrated into Makefile targets or documented as standalone utilities
2. WHEN the CI workflow needs validation THEN it SHALL use `make validate` instead of calling scripts directly
3. WHEN quality checks are needed THEN the CI SHALL use `make quality` instead of the `scripts/quality_check.sh` script
4. IF scripts are kept THEN they SHALL be documented and their relationship to Makefile targets SHALL be clear