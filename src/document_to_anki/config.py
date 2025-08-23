"""Configuration management for Document to Anki CLI application."""

import os
from dataclasses import dataclass
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    """Exception raised for model configuration issues."""

    pass


class LanguageValidationError(Exception):
    """Exception raised for language configuration issues."""

    def __init__(self, language: str, supported_languages: list[str]):
        self.language = language
        self.supported_languages = supported_languages
        super().__init__(f"Unsupported language '{language}'. Supported languages: {', '.join(supported_languages)}")


@dataclass
class LanguageInfo:
    """Language information structure."""

    code: str  # ISO 639-1 code (e.g., "en", "fr")
    name: str  # Display name (e.g., "English", "French")
    prompt_key: str  # Internal key for prompt templates


class LanguageConfig:
    """Handles language configuration and validation."""

    SUPPORTED_LANGUAGES: dict[str, dict[str, str]] = {
        "english": {"code": "en", "name": "English", "prompt_key": "english"},
        "en": {"code": "en", "name": "English", "prompt_key": "english"},
        "french": {"code": "fr", "name": "French", "prompt_key": "french"},
        "fr": {"code": "fr", "name": "French", "prompt_key": "french"},
        "italian": {"code": "it", "name": "Italian", "prompt_key": "italian"},
        "it": {"code": "it", "name": "Italian", "prompt_key": "italian"},
        "german": {"code": "de", "name": "German", "prompt_key": "german"},
        "de": {"code": "de", "name": "German", "prompt_key": "german"},
    }

    DEFAULT_LANGUAGE = "english"

    @classmethod
    def normalize_language(cls, language: str) -> str:
        """Normalize language input to standard format.

        Args:
            language: Language code or name to normalize

        Returns:
            Normalized language key (lowercase)

        Raises:
            LanguageValidationError: If language is not supported
        """
        if not language:
            return cls.DEFAULT_LANGUAGE

        normalized = language.lower().strip()

        if normalized not in cls.SUPPORTED_LANGUAGES:
            raise LanguageValidationError(language, cls.get_supported_languages_list())

        return normalized

    @classmethod
    def validate_language(cls, language: str) -> bool:
        """Validate if language is supported.

        Args:
            language: Language code or name to validate

        Returns:
            True if language is supported, False otherwise
        """
        if not language:
            return True  # Empty language defaults to English

        normalized = language.lower().strip()
        return normalized in cls.SUPPORTED_LANGUAGES

    @classmethod
    def get_language_name(cls, language: str) -> str:
        """Get display name for language.

        Args:
            language: Language code or name

        Returns:
            Display name of the language

        Raises:
            LanguageValidationError: If language is not supported
        """
        normalized = cls.normalize_language(language)
        return cls.SUPPORTED_LANGUAGES[normalized]["name"]

    @classmethod
    def get_language_code(cls, language: str) -> str:
        """Get ISO 639-1 code for language.

        Args:
            language: Language code or name

        Returns:
            ISO 639-1 language code

        Raises:
            LanguageValidationError: If language is not supported
        """
        normalized = cls.normalize_language(language)
        return cls.SUPPORTED_LANGUAGES[normalized]["code"]

    @classmethod
    def get_prompt_key(cls, language: str) -> str:
        """Get prompt template key for language.

        Args:
            language: Language code or name

        Returns:
            Prompt template key for the language

        Raises:
            LanguageValidationError: If language is not supported
        """
        normalized = cls.normalize_language(language)
        return cls.SUPPORTED_LANGUAGES[normalized]["prompt_key"]

    @classmethod
    def get_language_info(cls, language: str) -> LanguageInfo:
        """Get structured language information.

        Args:
            language: Language code or name

        Returns:
            LanguageInfo object with code, name, and prompt_key

        Raises:
            LanguageValidationError: If language is not supported
        """
        normalized = cls.normalize_language(language)
        lang_data = cls.SUPPORTED_LANGUAGES[normalized]
        return LanguageInfo(code=lang_data["code"], name=lang_data["name"], prompt_key=lang_data["prompt_key"])

    @classmethod
    def get_supported_languages_list(cls) -> list[str]:
        """Get list of supported language codes and names.

        Returns:
            List of supported language identifiers
        """
        # Return unique language names and codes
        seen = set()
        languages = []
        for lang_data in cls.SUPPORTED_LANGUAGES.values():
            if lang_data["name"] not in seen:
                languages.append(f"{lang_data['name']} ({lang_data['code']})")
                seen.add(lang_data["name"])
        return sorted(languages)

    @classmethod
    def get_all_language_keys(cls) -> list[str]:
        """Get all supported language keys (including aliases).

        Returns:
            List of all supported language keys
        """
        return list(cls.SUPPORTED_LANGUAGES.keys())


class ModelConfig:
    """Handles LLM model configuration and validation."""

    SUPPORTED_MODELS: dict[str, str] = {
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
        "openai/gpt-4o": "OPENAI_API_KEY",
    }

    DEFAULT_MODEL = "gemini/gemini-2.5-flash"

    @classmethod
    def get_model_from_env(cls) -> str:
        """Get model from MODEL environment variable or return default."""
        return os.getenv("MODEL", cls.DEFAULT_MODEL)

    @classmethod
    def validate_model_config(cls, model: str) -> bool:
        """Validate that model is supported and API key is available."""
        if model not in cls.SUPPORTED_MODELS:
            return False

        required_key = cls.SUPPORTED_MODELS[model]
        return os.getenv(required_key) is not None

    @classmethod
    def get_supported_models(cls) -> list[str]:
        """Return list of supported model identifiers."""
        return list(cls.SUPPORTED_MODELS.keys())

    @classmethod
    def get_required_api_key(cls, model: str) -> str | None:
        """Get the required API key environment variable name for a model."""
        return cls.SUPPORTED_MODELS.get(model)

    @classmethod
    def validate_and_get_model(cls) -> str:
        """Validate model configuration and return the model to use.

        Raises:
            ConfigurationError: If model is invalid or API key is missing.
        """
        model = cls.get_model_from_env()

        if model not in cls.SUPPORTED_MODELS:
            supported = ", ".join(cls.get_supported_models())
            raise ConfigurationError(f"Unsupported model '{model}'. Supported models: {supported}")

        if not cls.validate_model_config(model):
            required_key = cls.get_required_api_key(model)
            raise ConfigurationError(
                f"Missing API key for model '{model}'. Please set the {required_key} environment variable."
            )

        return model


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # LLM Configuration
    gemini_api_key: str | None = Field(None, alias="GEMINI_API_KEY")
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    model: str = Field("gemini/gemini-2.5-flash", alias="MODEL")

    # Language Configuration
    cardlang: str = Field("english", alias="CARDLANG")

    # Application Settings
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    verbose: bool = Field(False, alias="VERBOSE")
    max_file_size_mb: int = Field(50, alias="MAX_FILE_SIZE_MB")
    max_batch_size: int = Field(10, alias="MAX_BATCH_SIZE")

    # Web Interface Settings
    web_host: str = Field("127.0.0.1", alias="WEB_HOST")  # nosec B104 - Default to localhost for security
    web_port: int = Field(8000, alias="WEB_PORT")
    web_debug: bool = Field(False, alias="WEB_DEBUG")
    secret_key: str = Field("change-this-in-production", alias="SECRET_KEY")

    # LLM Processing Settings
    max_tokens_per_request: int = Field(4000, alias="MAX_TOKENS_PER_REQUEST")
    flashcards_per_chunk: int = Field(10, alias="FLASHCARDS_PER_CHUNK")
    llm_max_retries: int = Field(3, alias="LLM_MAX_RETRIES")
    llm_retry_delay: float = Field(1.0, alias="LLM_RETRY_DELAY")
    llm_timeout: int = Field(30, alias="LLM_TIMEOUT")

    # File Processing Settings
    supported_extensions: str = Field(".pdf,.docx,.txt,.md", alias="SUPPORTED_EXTENSIONS")
    temp_dir: Path = Field(Path.home() / ".cache" / "document_to_anki", alias="TEMP_DIR")  # nosec B108 - Use user cache dir
    cleanup_temp_files: bool = Field(True, alias="CLEANUP_TEMP_FILES")

    # Export Settings
    output_dir: Path = Field(Path("./exports"), alias="OUTPUT_DIR")
    csv_delimiter: str = Field(",", alias="CSV_DELIMITER")
    csv_encoding: str = Field("utf-8", alias="CSV_ENCODING")
    include_metadata: bool = Field(True, alias="INCLUDE_METADATA")

    # Development Settings
    disable_telemetry: bool = Field(True, alias="DISABLE_TELEMETRY")
    dev_mode: bool = Field(False, alias="DEV_MODE")
    mock_llm_responses: bool = Field(False, alias="MOCK_LLM_RESPONSES")

    # Performance Settings
    worker_processes: int = Field(4, alias="WORKER_PROCESSES")
    memory_limit_mb: int = Field(512, alias="MEMORY_LIMIT_MB")
    enable_caching: bool = Field(True, alias="ENABLE_CACHING")
    cache_dir: Path = Field(Path("./.cache"), alias="CACHE_DIR")
    cache_expiration_hours: int = Field(24, alias="CACHE_EXPIRATION_HOURS")

    @field_validator("supported_extensions")
    @classmethod
    def parse_extensions(cls, v: str) -> str:
        """Parse comma-separated extensions string."""
        return v  # Keep as string, parse when needed

    def get_supported_extensions(self) -> list[str]:
        """Get supported extensions as a list."""
        return [ext.strip() for ext in self.supported_extensions.split(",")]

    @field_validator("temp_dir", "output_dir", "cache_dir", mode="before")
    @classmethod
    def parse_path(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model format."""
        if not v or "/" not in v:
            raise ValueError("Model must be in format 'provider/model-name'")
        return v

    @field_validator("cardlang")
    @classmethod
    def validate_cardlang(cls, v: str) -> str:
        """Validate and normalize language configuration."""
        if not v or not v.strip():
            return LanguageConfig.DEFAULT_LANGUAGE  # Default fallback to English

        try:
            return LanguageConfig.normalize_language(v)
        except LanguageValidationError as e:
            raise ValueError(str(e)) from e

    def get_api_key(self) -> str | None:
        """Get the appropriate API key based on the model."""
        if self.model.startswith("gemini/"):
            return self.gemini_api_key
        elif self.model.startswith("openai/"):
            return self.openai_api_key
        else:
            # Try to determine from model name
            if "gemini" in self.model.lower():
                return self.gemini_api_key
            elif "gpt" in self.model.lower() or "openai" in self.model.lower():
                return self.openai_api_key
        return None

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        directories = [self.temp_dir, self.output_dir, self.cache_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def memory_limit_bytes(self) -> int:
        """Get memory limit in bytes."""
        return self.memory_limit_mb * 1024 * 1024

    def get_language_info(self) -> LanguageInfo:
        """Get structured language information.

        Returns:
            LanguageInfo object with code, name, and prompt_key for the configured language
        """
        return LanguageConfig.get_language_info(self.cardlang)

    def get_language_name(self) -> str:
        """Get display name for the configured language.

        Returns:
            Display name of the configured language
        """
        return LanguageConfig.get_language_name(self.cardlang)

    def get_language_code(self) -> str:
        """Get ISO 639-1 code for the configured language.

        Returns:
            ISO 639-1 language code for the configured language
        """
        return LanguageConfig.get_language_code(self.cardlang)

    def get_prompt_key(self) -> str:
        """Get prompt template key for the configured language.

        Returns:
            Prompt template key for the configured language
        """
        return LanguageConfig.get_prompt_key(self.cardlang)


# Global settings instance
settings = Settings()  # type: ignore[call-arg]
