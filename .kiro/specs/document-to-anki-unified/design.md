# Design Document

## Overview

The Document-to-Anki CLI application is a modern Python tool that converts various document formats into Anki flashcards using configurable Large Language Models. The system provides both CLI and web interfaces with multi-language support, allowing users to upload documents, preview/edit generated flashcards in their preferred language, and export them as Anki-compatible CSV files.

The application follows modern Python development practices using Python 3.12+, uv for package management, and incorporates best-in-class tools for development, testing, and user experience.

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
document-to-anki-cli/
├── src/
│   ├── document_to_anki/
│   │   ├── __init__.py
│   │   ├── config.py             # Unified configuration management
│   │   ├── cli/
│   │   │   ├── __init__.py
│   │   │   └── main.py           # CLI entry point
│   │   ├── web/
│   │   │   ├── __init__.py
│   │   │   ├── app.py            # FastAPI web application
│   │   │   └── static/           # Web assets
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── flashcard_generator.py
│   │   │   └── llm_client.py     # Multi-language LLM integration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── flashcard.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_handler.py
│   │       └── text_extractor.py
├── tests/
├── pyproject.toml
└── README.md
```

### Key Architectural Principles

1. **Separation of Concerns**: CLI, web, and core logic are separated into distinct modules
2. **Dependency Injection**: Core services are injected to enable testing and flexibility
3. **Single Responsibility**: Each module has a clear, focused purpose
4. **Testability**: All components are designed to be easily testable with pytest-mock
5. **Configuration-Driven**: Both model and language selection are environment-driven

## Components and Interfaces

### Configuration Management

The application supports configurable LLM models and languages through environment variables, providing flexibility in model selection, cost optimization, and language preferences.

#### Unified Settings Class

```python
class Settings(BaseSettings):
    """Unified configuration management for the application."""
    
    # Model Configuration
    model: str = Field("gemini/gemini-2.5-flash", alias="MODEL")
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    
    # Language Configuration
    cardlang: str = Field("english", alias="CARDLANG")
    
    # Application Settings
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    max_tokens: int = Field(4000, alias="MAX_TOKENS")
    
    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model configuration and API key availability."""
        # Implementation details below
        
    @field_validator("cardlang")
    @classmethod
    def validate_cardlang(cls, v: str) -> str:
        """Validate and normalize language configuration."""
        # Implementation details below
```

#### Model Configuration Strategy

```python
class ModelConfig:
    """Handles LLM model configuration and validation."""
    
    SUPPORTED_MODELS = {
        "gemini/gemini-2.5-flash": "GEMINI_API_KEY",
        "gemini/gemini-2.5-pro": "GEMINI_API_KEY",
        "openai/gpt-4": "OPENAI_API_KEY", 
        "openai/gpt-3.5-turbo": "OPENAI_API_KEY",
        "openai/gpt-4.1": "OPENAI_API_KEY",
        "openai/gpt-4.1-mini": "OPENAI_API_KEY",
        "openai/gpt-4.1-nano": "OPENAI_API_KEY",
        "openai/gpt-5": "OPENAI_API_KEY",
        "openai/gpt-5-mini": "OPENAI_API_KEY",
        "openai/gpt-5-nano": "OPENAI_API_KEY",
        "openai/gpt-4o": "OPENAI_API_KEY"
    }
    
    DEFAULT_MODEL = "gemini/gemini-2.5-flash"
    
    @classmethod
    def validate_model_config(cls, model: str) -> bool:
        """Validate that model is supported and API key is available."""
        if model not in cls.SUPPORTED_MODELS:
            return False
        
        required_key = cls.SUPPORTED_MODELS[model]
        return os.getenv(required_key) is not None
```

#### Language Configuration Strategy

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
        normalized = language.lower().strip()
        if normalized in cls.SUPPORTED_LANGUAGES:
            return cls.SUPPORTED_LANGUAGES[normalized]["code"]
        raise ValueError(f"Unsupported language: {language}")
    
    @classmethod
    def validate_language(cls, language: str) -> bool:
        """Validate if language is supported."""
        return language.lower().strip() in cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def get_language_name(cls, language: str) -> str:
        """Get display name for language."""
        normalized = language.lower().strip()
        if normalized in cls.SUPPORTED_LANGUAGES:
            return cls.SUPPORTED_LANGUAGES[normalized]["name"]
        return language
```

### Core Components

#### Enhanced LLM Client Component

```python
class LLMClient:
    """Multi-language, multi-model LLM client."""
    
    def __init__(self, model: str | None = None, language: str = "english", max_tokens: int = 4000):
        """Initialize LLM client with model and language configuration."""
        self.settings = Settings()
        self.model = model or self.settings.model
        self.language = LanguageConfig.normalize_language(language or self.settings.cardlang)
        self.max_tokens = max_tokens
        
        # Validate configuration
        if not ModelConfig.validate_model_config(self.model):
            raise ConfigurationError(f"Invalid model configuration: {self.model}")
    
    def _get_prompt_template(self, language: str, content_type: str = "general") -> str:
        """Get language-specific prompt template."""
        templates = {
            "en": self._get_english_prompt_template(content_type),
            "fr": self._get_french_prompt_template(content_type),
            "it": self._get_italian_prompt_template(content_type),
            "de": self._get_german_prompt_template(content_type),
        }
        return templates.get(language, templates["en"])
    
    async def generate_flashcards_from_text(
        self, 
        text: str, 
        language: str | None = None, 
        content_type: str = "general"
    ) -> list[dict[str, str]]:
        """Generate flashcards with configurable language support."""
        target_language = language or self.language
        prompt = self._create_flashcard_prompt(text, target_language, content_type)
        
        # Generate flashcards using litellm
        response = await self._call_llm(prompt)
        flashcards = self._parse_response(response)
        
        # Validate language output
        validated_flashcards = self._validate_language_output(flashcards, target_language)
        
        return validated_flashcards
    
    def _validate_language_output(self, flashcards: list[dict], target_language: str) -> list[dict]:
        """Validate that flashcards are in the correct language."""
        # Language-specific validation logic
        # Retry generation if validation fails
        pass
```

#### Language-Specific Prompt Templates

```python
def _get_english_prompt_template(self, content_type: str) -> str:
    """English flashcard generation prompt."""
    return """
    You are an expert at creating flashcards for learning.
    Analyze the provided text and create high-quality flashcards in English.
    
    Instructions:
    1. All questions and answers MUST be in English
    2. Use proper English grammar and appropriate vocabulary
    3. Create clear, concise questions with accurate answers
    4. Generate a mix of question-answer and cloze deletion cards
    5. Focus on the most important information in the text
    
    Text to analyze:
    {text}
    """

def _get_french_prompt_template(self, content_type: str) -> str:
    """French flashcard generation prompt."""
    return """
    Vous êtes un expert en création de cartes mémoire (flashcards) pour l'apprentissage.
    Analysez le texte fourni et créez des cartes mémoire en français de haute qualité.
    
    Instructions importantes:
    1. Toutes les questions et réponses DOIVENT être en français
    2. Utilisez une grammaire française correcte et un vocabulaire approprié
    3. Créez des questions claires et concises avec des réponses précises
    4. Générez un mélange de cartes question-réponse et de cartes à trous (cloze deletion)
    5. Concentrez-vous sur les informations les plus importantes du texte
    
    Texte à analyser:
    {text}
    """

def _get_italian_prompt_template(self, content_type: str) -> str:
    """Italian flashcard generation prompt."""
    return """
    Sei un esperto nella creazione di flashcard per l'apprendimento.
    Analizza il testo fornito e crea flashcard di alta qualità in italiano.
    
    Istruzioni importanti:
    1. Tutte le domande e risposte DEVONO essere in italiano
    2. Usa una grammatica italiana corretta e un vocabolario appropriato
    3. Crea domande chiare e concise con risposte accurate
    4. Genera un mix di carte domanda-risposta e carte cloze deletion
    5. Concentrati sulle informazioni più importanti del testo
    
    Testo da analizzare:
    {text}
    """

def _get_german_prompt_template(self, content_type: str) -> str:
    """German flashcard generation prompt."""
    return """
    Sie sind ein Experte für die Erstellung von Lernkarten (Flashcards).
    Analysieren Sie den bereitgestellten Text und erstellen Sie hochwertige Lernkarten auf Deutsch.
    
    Wichtige Anweisungen:
    1. Alle Fragen und Antworten MÜSSEN auf Deutsch sein
    2. Verwenden Sie korrekte deutsche Grammatik und angemessenes Vokabular
    3. Erstellen Sie klare, prägnante Fragen mit genauen Antworten
    4. Generieren Sie eine Mischung aus Frage-Antwort- und Lückentext-Karten
    5. Konzentrieren Sie sich auf die wichtigsten Informationen im Text
    
    Zu analysierender Text:
    {text}
    """
```

### Testing Strategy with pytest-mock

#### Comprehensive Mocking Strategy

```python
# Example test structure using pytest-mock
class TestLLMClientLanguage:
    def test_language_specific_prompts(self, mocker):
        """Test generation of language-specific prompts using pytest-mock."""
        # Mock litellm response
        mock_response = mocker.patch('litellm.acompletion')
        mock_response.return_value = AsyncMock(
            choices=[Mock(message=Mock(content='{"flashcards": [...]}'))]
        )
        
        client = LLMClient(language="french")
        # Test implementation
    
    def test_model_configuration_validation(self, mocker):
        """Test model configuration validation using pytest-mock."""
        # Mock environment variables
        mocker.patch.dict(os.environ, {
            'MODEL': 'gemini/gemini-2.5-pro',
            'GEMINI_API_KEY': 'test-key'
        })
        
        # Test model validation
        client = LLMClient()
        assert client.model == 'gemini/gemini-2.5-pro'
    
    def test_language_validation_retry(self, mocker):
        """Test language validation and retry logic using pytest-mock."""
        # Mock LLM responses - first invalid, then valid
        mock_responses = [
            '{"flashcards": [{"question": "What is...?", "answer": "It is..."}]}',  # English
            '{"flashcards": [{"question": "Qu\'est-ce que...?", "answer": "C\'est..."}]}'  # French
        ]
        
        mock_completion = mocker.patch('litellm.acompletion')
        mock_completion.side_effect = [
            AsyncMock(choices=[Mock(message=Mock(content=resp))]) 
            for resp in mock_responses
        ]
        
        client = LLMClient(language="french")
        # Test retry logic
```

#### Test Coverage Requirements

1. **Unit Tests**: All components tested in isolation using pytest-mock
2. **Integration Tests**: Component interactions with mocked external dependencies
3. **Language Tests**: Each supported language validated with appropriate test data
4. **Configuration Tests**: All environment variable combinations tested
5. **Error Handling Tests**: All error conditions and edge cases covered

### Error Handling

#### Comprehensive Error Strategy

```python
class DocumentToAnkiError(Exception):
    """Base exception for the application"""
    pass

class FileProcessingError(DocumentToAnkiError):
    """Errors related to file processing"""
    pass

class LLMError(DocumentToAnkiError):
    """Errors related to LLM communication"""
    pass

class ConfigurationError(DocumentToAnkiError):
    """Errors related to model and language configuration"""
    pass

class ValidationError(DocumentToAnkiError):
    """Errors related to data validation"""
    pass

class LanguageValidationError(DocumentToAnkiError):
    """Errors related to language processing and validation"""
    pass
```

### Language Validation System

#### Multi-Language Validation

```python
class LanguageValidator:
    """Validates LLM output for correct language usage."""
    
    def __init__(self):
        self.validators = {
            "en": self._validate_english,
            "fr": self._validate_french,
            "it": self._validate_italian,
            "de": self._validate_german,
        }
    
    def validate_flashcard_language(self, flashcard: dict, target_language: str) -> bool:
        """Validate that flashcard is in the correct language."""
        validator = self.validators.get(target_language, self._validate_english)
        return (validator(flashcard['question']) and 
                validator(flashcard['answer']))
    
    def _validate_french(self, text: str) -> bool:
        """Validate French text using linguistic patterns."""
        french_indicators = [
            r'\b(le|la|les|un|une|des)\b',  # Articles
            r'\b(est|sont|était|étaient)\b',  # Common verbs
            r'\b(que|qui|dont|où)\b',  # Relative pronouns
            r'\b(avec|dans|pour|sur|sous)\b'  # Prepositions
        ]
        
        score = sum(1 for pattern in french_indicators 
                   if re.search(pattern, text.lower()))
        return score >= 2
    
    def _validate_english(self, text: str) -> bool:
        """Validate English text using linguistic patterns."""
        english_indicators = [
            r'\b(the|a|an)\b',  # Articles
            r'\b(is|are|was|were)\b',  # Common verbs
            r'\b(that|which|who|where)\b',  # Relative pronouns
            r'\b(with|in|for|on|under)\b'  # Prepositions
        ]
        
        score = sum(1 for pattern in english_indicators 
                   if re.search(pattern, text.lower()))
        return score >= 2
    
    # Similar methods for Italian and German...
```

## Design Decisions and Rationales

### 1. Unified Configuration Approach

**Decision**: Consolidate model and language configuration in a single Settings class
**Rationale**: 
- Maintains consistency with existing configuration patterns
- Simplifies dependency injection and testing
- Provides single source of truth for all configuration
- Enables easy validation of configuration combinations

### 2. Multi-Language Prompt Architecture

**Decision**: Separate prompt templates per language with shared structure
**Rationale**:
- Ensures proper grammar and vocabulary for each language
- Allows language-specific optimizations and cultural context
- Maintains consistency in flashcard quality across languages
- Enables easy addition of new languages

### 3. pytest-mock Standardization

**Decision**: Standardize on pytest-mock for all mocking operations
**Rationale**:
- More Pythonic and intuitive than unittest.mock
- Better integration with pytest fixtures and parametrization
- Cleaner syntax and better error messages
- Follows modern Python testing best practices

### 4. Language Validation Strategy

**Decision**: Validate language at both configuration and response time
**Rationale**:
- Early validation prevents runtime errors
- Response validation ensures quality control
- Retry mechanism improves success rate
- Clear error messages improve user experience

### 5. Backward Compatibility Strategy

**Decision**: Default to English, maintain all existing functionality
**Rationale**:
- English is more universally understood
- Smooth migration path for existing users
- Preserves all existing model configuration features
- Aligns with international software standards

This unified design ensures that both model and language configuration work seamlessly together while maintaining the high-quality flashcard generation and comprehensive testing that the application requires.