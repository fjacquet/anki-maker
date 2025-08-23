# Requirements Document

## Introduction

This feature involves adding configurable language support to the document-to-anki-cli application. Currently, the system is hardcoded to generate flashcards in French. This enhancement will allow users to configure the output language for flashcard generation through environment variables, supporting French, English, Italian, and German languages. The language configuration will be integrated into the existing configuration system and will affect how the LLM generates flashcard content.

## Requirements

### Requirement 1

**User Story:** As a user, I want to configure the flashcard output language through environment variables, so that I can generate flashcards in my preferred language without modifying code.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL read a CARDLANG environment variable to determine the flashcard output language
2. WHEN CARDLANG is set to a supported language THEN the system SHALL use that language for all flashcard generation
3. WHEN CARDLANG is not set THEN the system SHALL default to English as the fallback language
4. WHEN an invalid language is specified THEN the system SHALL display a clear error message listing supported languages
5. WHEN the language is configured THEN the system SHALL validate the language code before processing any documents

### Requirement 2

**User Story:** As a multilingual user, I want support for French, English, Italian, and German languages, so that I can study content in any of these commonly used languages.

#### Acceptance Criteria

1. WHEN CARDLANG is set to "french" or "fr" THEN the system SHALL generate flashcards in French language
2. WHEN CARDLANG is set to "english" or "en" THEN the system SHALL generate flashcards in English language
3. WHEN CARDLANG is set to "italian" or "it" THEN the system SHALL generate flashcards in Italian language
4. WHEN CARDLANG is set to "german" or "de" THEN the system SHALL generate flashcards in German language
5. WHEN processing any document content THEN the system SHALL instruct the LLM to generate flashcards in the configured language regardless of the source document language

### Requirement 3

**User Story:** As a developer, I want the language configuration to be integrated into the existing Settings class, so that it follows the same patterns as other configuration options.

#### Acceptance Criteria

1. WHEN adding language configuration THEN the system SHALL add a cardlang field to the Settings class with proper validation
2. WHEN validating language configuration THEN the system SHALL use Pydantic field validators to ensure only supported languages are accepted
3. WHEN the configuration is loaded THEN the system SHALL normalize language codes to a consistent format (e.g., lowercase)
4. WHEN accessing language configuration THEN the system SHALL provide helper methods to get language names and codes
5. WHEN the .env.example file is updated THEN it SHALL include documentation for the CARDLANG variable with examples

### Requirement 4

**User Story:** As a user, I want the LLM prompts to be updated to use the configured language, so that flashcards are generated with proper grammar and vocabulary in my chosen language.

#### Acceptance Criteria

1. WHEN generating flashcards THEN the system SHALL modify LLM prompts to specify the target language for output
2. WHEN creating question-answer pairs THEN the system SHALL ensure proper grammar and vocabulary usage in the configured language
3. WHEN creating cloze deletion cards THEN the system SHALL use appropriate sentence structure and context for the configured language
4. WHEN the LLM generates responses THEN the system SHALL validate that the output is in the correct language
5. WHEN language validation fails THEN the system SHALL log a warning and optionally retry the request

### Requirement 5

**User Story:** As a quality assurance engineer, I want comprehensive tests for the language configuration feature, so that I can ensure it works correctly across all supported languages.

#### Acceptance Criteria

1. WHEN testing language configuration THEN the system SHALL include unit tests for all supported language codes
2. WHEN testing validation THEN the system SHALL include tests for invalid language codes and error handling
3. WHEN testing LLM integration THEN the system SHALL include tests that verify prompts are correctly modified for each language
4. WHEN testing configuration loading THEN the system SHALL include tests for environment variable parsing and defaults
5. WHEN running integration tests THEN the system SHALL verify that flashcards are generated in the correct language for each supported option

### Requirement 6

**User Story:** As a user, I want clear documentation about language configuration, so that I understand how to set up and use different languages.

#### Acceptance Criteria

1. WHEN updating documentation THEN the system SHALL include examples of setting CARDLANG in the .env.example file
2. WHEN providing help text THEN the CLI SHALL display supported language options in help messages
3. WHEN errors occur THEN the system SHALL provide clear guidance on valid language codes and formats
4. WHEN documenting the feature THEN the system SHALL explain how language affects flashcard generation
5. WHEN updating the README THEN it SHALL include examples of using different languages

### Requirement 7

**User Story:** As a developer, I want backward compatibility with existing configurations, so that current users are not affected by the language configuration changes.

#### Acceptance Criteria

1. WHEN no CARDLANG is specified THEN the system SHALL maintain current behavior by defaulting to English
2. WHEN existing .env files are used THEN the system SHALL continue to work without requiring CARDLANG configuration
3. WHEN upgrading from previous versions THEN users SHALL not need to modify their existing configuration
4. WHEN the French hardcoded behavior exists THEN it SHALL be replaced by the configurable system while maintaining French as an option
5. WHEN configuration validation fails THEN the system SHALL provide migration guidance to users

### Requirement 8

**User Story:** As a user, I want the web interface to respect the language configuration, so that both CLI and web interfaces provide consistent behavior.

#### Acceptance Criteria

1. WHEN using the web interface THEN the system SHALL use the same CARDLANG configuration as the CLI
2. WHEN displaying flashcards in the web interface THEN they SHALL be shown in the configured language
3. WHEN editing flashcards through the web interface THEN the interface SHALL maintain the language consistency
4. WHEN errors occur in the web interface THEN error messages SHALL be displayed appropriately (though UI language may remain English)
5. WHEN processing files through the web interface THEN the same language configuration SHALL apply as in CLI mode