# Implementation Plan

- [x] 1. Create LanguageConfig utility class for language management
  - Implement LanguageConfig class with supported language mappings and validation methods
  - Create methods for language normalization, validation, and information retrieval
  - Add comprehensive error handling for invalid language codes
  - Write unit tests for all LanguageConfig methods
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.3, 3.4_

- [x] 2. Extend Settings class with language configuration
  - Add cardlang field to Settings class with CARDLANG environment variable alias
  - Implement Pydantic field validator for cardlang using LanguageConfig validation
  - Add helper methods to Settings for language information retrieval
  - Ensure default fallback to English when CARDLANG not set
  - Write unit tests for Settings language configuration validation
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 7.1, 7.2_

- [x] 3. Update .env.example with CARDLANG documentation
  - Add CARDLANG variable to .env.example file with clear documentation
  - Include examples of all supported language codes and formats
  - Provide usage guidance and examples for different languages
  - Document the default behavior when CARDLANG is not set
  - _Requirements: 3.5, 6.1, 6.4_

- [x] 4. Create language-specific prompt templates
  - Implement prompt templates for English, French, Italian, and German languages
  - Ensure proper grammar, vocabulary, and cultural context for each language
  - Create separate templates for different content types (academic, technical, general)
  - Add validation to ensure prompts specify target language clearly
  - Write unit tests for prompt template generation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.2, 4.3_

- [x] 5. Modify LLMClient constructor to accept language parameter
  - Update LLMClient __init__ method to accept language parameter with default
  - Integrate LanguageConfig for language validation and normalization
  - Maintain backward compatibility with existing LLMClient usage
  - Add language information to LLMClient logging and debugging
  - Write unit tests for LLMClient language initialization
  - _Requirements: 1.2, 3.3, 7.3, 7.4_

- [x] 6. Update LLMClient prompt generation methods
  - Modify _create_flashcard_prompt method to use language-specific templates
  - Replace hardcoded French prompt with configurable language system
  - Ensure prompt generation uses correct language template based on configuration
  - Add content type parameter support for specialized prompts
  - Write unit tests for language-specific prompt generation
  - _Requirements: 4.1, 4.2, 4.3, 7.4_

- [x] 7. Enhance generate_flashcards_from_text method with language support
  - Update method signature to accept optional language parameter
  - Integrate language configuration from Settings when language not explicitly provided
  - Ensure flashcard generation uses configured language for all operations
  - Maintain backward compatibility with existing method calls
  - Write unit tests for flashcard generation with different languages
  - _Requirements: 1.2, 2.5, 4.1, 7.3_

- [x] 8. Implement LLM response language validation
  - Add validation logic to verify generated flashcards are in correct language
  - Implement retry mechanism for language validation failures
  - Add comprehensive logging for language validation results and failures
  - Create fallback behavior when language validation consistently fails
  - Write unit tests for response validation and retry logic
  - _Requirements: 4.4, 4.5_

- [x] 9. Update CLI help text and error messages
  - Add language configuration information to CLI help text
  - Include supported languages list in help messages and error outputs
  - Provide clear examples of CARDLANG usage in CLI documentation
  - Enhance error messages with specific guidance for language configuration
  - Write integration tests for CLI help text and error message display
  - _Requirements: 1.4, 6.2, 6.3_

- [ ] 10. Integrate language configuration in web interface
  - Ensure web application uses same Settings instance and language configuration
  - Display current language configuration in web interface
  - Maintain language consistency across all web interface flashcard operations
  - Update web interface error handling to show language-related errors appropriately
  - Write integration tests for web interface language consistency
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 11. Create comprehensive language configuration tests
  - Write unit tests for all supported language codes and validation scenarios
  - Create tests for invalid language codes and error handling behavior
  - Implement integration tests for environment variable parsing and defaults
  - Add end-to-end tests verifying flashcard generation in each supported language
  - Create performance tests to ensure language processing doesn't impact performance
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 12. Update documentation and migration guidance
  - Update README with language configuration examples and usage instructions
  - Create migration guide for users upgrading from hardcoded French behavior
  - Document language configuration impact on flashcard generation quality
  - Add troubleshooting section for common language configuration issues
  - Provide clear examples of using different languages in various scenarios
  - _Requirements: 6.4, 6.5, 7.5_