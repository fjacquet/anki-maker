# Multi-Language Configuration Design Document

## Overview

This design document outlines the implementation of configurable language support for the document-to-anki-cli application. The feature will transform the current hardcoded French language generation into a flexible, environment-variable-driven system supporting French, English, Italian, and German languages. The design integrates seamlessly with the existing Pydantic-based configuration system and maintains backward compatibility while providing clear error handling and validation.

## Architecture

### High-Level Architecture

The multi-language configuration feature follows the existing application architecture patterns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Environment   │───▶│   Settings       │───▶│   LLMClient     │
│   Variables     │    │   (config.py)    │    │   Prompt Gen    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Language       │
                       │   Validation     │
                       └──────────────────┘
```

### Integration Points

1. **Configuration Layer**: Extends the existing `Settings` class in `config.py`
2. **LLM Client Layer**: Modifies `LLMClient` in `llm_client.py` to use configurable language prompts
3. **CLI Layer**: Updates help text and error messages to include language options
4. **Web Layer**: Ensures web interface respects the same language configuration

## Components and Interfaces

### 1. Language Configuration Component

**Location**: `src/document_to_anki/config.py`

**New Fields in Settings Class**:
```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Language Configuration
    cardlang: str = Field("english", alias="CARDLANG")
    
    @field_validator("cardlang")
    @classmethod
    def validate_cardlang(cls, v: str) -> str:
        """Validate and normalize language configuration."""
        # Implementation details in next section
```

**Language Mapping Utility**:
```python
class LanguageConfig:
    """Handles language configuration and validation."""
    
    SUPPORTED_LANGUAGES = {
        "english": {"code": "en", "name": "English"},
        "en": {"code": "en", "name": "English"},
        "french": {"code": "fr", "name": "French"},
        "fr": {"code": "fr", "name": "French"},
        "italian": {"code": "it", "name": "Italian"},
        "it": {"code": "it", "name": "Italian"},
        "german": {"code": "de", "name": "German"},
        "de": {"code": "de", "name": "German"},
    }
    
    @classmethod
    def normalize_language(cls, language: str) -> str:
        """Normalize language input to standard format."""
        
    @classmethod
    def validate_language(cls, language: str) -> bool:
        """Validate if language is supported."""
        
    @classmethod
    def get_language_name(cls, language: str) -> str:
        """Get display name for language."""
        
    @classmethod
    def get_supported_languages_list(cls) -> list[str]:
        """Get list of supported language codes and names."""
```

### 2. Enhanced LLM Client Component

**Location**: `src/document_to_anki/core/llm_client.py`

**Modified Constructor**:
```python
class LLMClient:
    def __init__(self, model: str | None = None, max_tokens: int = 4000, language: str = "english"):
        """Initialize LLM client with language configuration."""
        # ... existing initialization ...
        self.language = LanguageConfig.normalize_language(language)
```

**Language-Specific Prompt Templates**:
```python
def _get_prompt_template(self, language: str, content_type: str = "general") -> str:
    """Get language-specific prompt template."""
    
def _create_flashcard_prompt(self, text: str, language: str, content_type: str = "general") -> str:
    """Create prompt with specified language instructions."""
```

**Updated Generation Method**:
```python
async def generate_flashcards_from_text(
    self, 
    text: str, 
    language: str | None = None, 
    content_type: str = "general"
) -> list[dict[str, str]]:
    """Generate flashcards with configurable language support."""
```

### 3. CLI Integration Component

**Location**: `src/document_to_anki/cli/main.py`

**Enhanced Help Text**:
- Add language configuration information to CLI help
- Include supported languages in error messages
- Provide examples of CARDLANG usage

**Error Handling**:
- Clear error messages for invalid language codes
- Guidance on setting environment variables
- Migration help for existing users

### 4. Web Interface Integration

**Location**: `src/document_to_anki/web/app.py`

**Configuration Consistency**:
- Use same Settings instance as CLI
- Display current language configuration in web interface
- Maintain language consistency across all flashcard operations

## Data Models

### Language Configuration Schema

```python
@dataclass
class LanguageInfo:
    """Language information structure."""
    code: str          # ISO 639-1 code (e.g., "en", "fr")
    name: str          # Display name (e.g., "English", "French")
    prompt_key: str    # Internal key for prompt templates

class LanguageValidationError(Exception):
    """Exception for language validation errors."""
    pass
```

### Enhanced Settings Model

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Language Configuration
    cardlang: str = Field("english", alias="CARDLANG")
    
    @field_validator("cardlang")
    @classmethod
    def validate_cardlang(cls, v: str) -> str:
        """Validate and normalize language configuration."""
        if not v:
            return "english"  # Default fallback
            
        normalized = v.lower().strip()
        
        if not LanguageConfig.validate_language(normalized):
            supported = ", ".join(LanguageConfig.get_supported_languages_list())
            raise ValueError(
                f"Unsupported language '{v}'. Supported languages: {supported}"
            )
        
        return LanguageConfig.normalize_language(normalized)
    
    def get_language_info(self) -> LanguageInfo:
        """Get structured language information."""
        return LanguageConfig.get_language_info(self.cardlang)
```

## Error Handling

### Validation Errors

**Language Validation**:
```python
class LanguageValidationError(Exception):
    """Raised when language configuration is invalid."""
    
    def __init__(self, language: str, supported_languages: list[str]):
        self.language = language
        self.supported_languages = supported_languages
        super().__init__(
            f"Unsupported language '{language}'. "
            f"Supported languages: {', '.join(supported_languages)}"
        )
```

**Configuration Loading Errors**:
- Clear error messages for invalid CARDLANG values
- Helpful suggestions for correct format
- Fallback to English with warning when possible

### Runtime Error Handling

**LLM Response Validation**:
- Validate that generated flashcards are in the correct language
- Log warnings for language mismatches
- Implement retry logic for language validation failures

**Graceful Degradation**:
- Fall back to English if language-specific prompts fail
- Maintain functionality even with configuration errors
- Provide clear user feedback about fallback behavior

## Testing Strategy

### Unit Tests

**Language Configuration Tests** (`test_language_config.py`):
```python
class TestLanguageConfig:
    def test_validate_supported_languages(self):
        """Test validation of all supported language codes."""
        
    def test_validate_invalid_languages(self):
        """Test validation rejects invalid language codes."""
        
    def test_normalize_language_codes(self):
        """Test language code normalization."""
        
    def test_language_info_retrieval(self):
        """Test language information retrieval."""
```

**Settings Integration Tests** (`test_settings_language.py`):
```python
class TestSettingsLanguage:
    def test_cardlang_field_validation(self):
        """Test CARDLANG field validation in Settings."""
        
    def test_environment_variable_parsing(self):
        """Test CARDLANG environment variable parsing."""
        
    def test_default_language_behavior(self):
        """Test default language when CARDLANG not set."""
```

**LLM Client Language Tests** (`test_llm_client_language.py`):
```python
class TestLLMClientLanguage:
    def test_language_specific_prompts(self):
        """Test generation of language-specific prompts."""
        
    def test_flashcard_generation_per_language(self):
        """Test flashcard generation for each supported language."""
        
    def test_language_validation_in_responses(self):
        """Test validation of LLM response language."""
```

### Integration Tests

**End-to-End Language Tests** (`test_e2e_language.py`):
```python
class TestE2ELanguage:
    def test_cli_language_configuration(self):
        """Test CLI with different language configurations."""
        
    def test_web_interface_language_consistency(self):
        """Test web interface respects language configuration."""
        
    def test_document_processing_with_languages(self):
        """Test full document processing pipeline with different languages."""
```

### Test Data and Fixtures

**Language Test Fixtures**:
- Sample documents in multiple languages
- Expected flashcard outputs for each language
- Mock LLM responses for language validation testing

## Design Decisions and Rationales

### 1. Environment Variable Approach

**Decision**: Use CARDLANG environment variable for configuration
**Rationale**: 
- Consistent with existing configuration pattern (MODEL, GEMINI_API_KEY, etc.)
- Allows easy configuration without code changes
- Supports both development and production environments
- Integrates seamlessly with existing pydantic-settings system

### 2. Language Code Normalization

**Decision**: Accept both full names ("english") and ISO codes ("en")
**Rationale**:
- User-friendly for non-technical users
- Flexible input format reduces configuration errors
- Maintains consistency with international standards
- Easy to extend for additional languages

### 3. Backward Compatibility Strategy

**Decision**: Default to English instead of French, maintain French as option
**Rationale**:
- English is more universally understood
- Removes hardcoded behavior while preserving French support
- Provides smooth migration path for existing users
- Aligns with international software standards

### 4. Prompt Template Architecture

**Decision**: Separate prompt templates per language with shared structure
**Rationale**:
- Ensures proper grammar and vocabulary for each language
- Allows language-specific optimizations
- Maintains consistency in flashcard quality
- Enables easy addition of new languages

### 5. Validation Strategy

**Decision**: Validate language at configuration load time and LLM response time
**Rationale**:
- Early validation prevents runtime errors
- Response validation ensures quality control
- Clear error messages improve user experience
- Graceful fallback maintains application stability

### 6. Integration with Existing Architecture

**Decision**: Extend existing classes rather than creating new modules
**Rationale**:
- Maintains architectural consistency
- Minimizes code duplication
- Leverages existing validation patterns
- Reduces complexity for maintenance

This design ensures that the multi-language configuration feature integrates seamlessly with the existing codebase while providing robust language support, clear error handling, and comprehensive testing coverage.