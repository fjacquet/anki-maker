"""Configuration management for Document to Anki CLI application."""

import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class ConfigurationError(Exception):
    """Exception raised for model configuration issues."""

    pass


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

    # LLM Configuration
    gemini_api_key: str | None = Field(None, env="GEMINI_API_KEY")
    openai_api_key: str | None = Field(None, env="OPENAI_API_KEY")
    model: str = Field("gemini/gemini-2.5-flash", env="MODEL")

    # Application Settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    verbose: bool = Field(False, env="VERBOSE")
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    max_batch_size: int = Field(10, env="MAX_BATCH_SIZE")

    # Web Interface Settings
    web_host: str = Field("0.0.0.0", env="WEB_HOST")
    web_port: int = Field(8000, env="WEB_PORT")
    web_debug: bool = Field(False, env="WEB_DEBUG")
    secret_key: str = Field("change-this-in-production", env="SECRET_KEY")

    # LLM Processing Settings
    max_tokens_per_request: int = Field(4000, env="MAX_TOKENS_PER_REQUEST")
    flashcards_per_chunk: int = Field(10, env="FLASHCARDS_PER_CHUNK")
    llm_max_retries: int = Field(3, env="LLM_MAX_RETRIES")
    llm_retry_delay: float = Field(1.0, env="LLM_RETRY_DELAY")
    llm_timeout: int = Field(30, env="LLM_TIMEOUT")

    # File Processing Settings
    supported_extensions: str = Field(".pdf,.docx,.txt,.md", env="SUPPORTED_EXTENSIONS")
    temp_dir: Path = Field(Path("/tmp/document_to_anki"), env="TEMP_DIR")
    cleanup_temp_files: bool = Field(True, env="CLEANUP_TEMP_FILES")

    # Export Settings
    output_dir: Path = Field(Path("./exports"), env="OUTPUT_DIR")
    csv_delimiter: str = Field(",", env="CSV_DELIMITER")
    csv_encoding: str = Field("utf-8", env="CSV_ENCODING")
    include_metadata: bool = Field(True, env="INCLUDE_METADATA")

    # Development Settings
    disable_telemetry: bool = Field(True, env="DISABLE_TELEMETRY")
    dev_mode: bool = Field(False, env="DEV_MODE")
    mock_llm_responses: bool = Field(False, env="MOCK_LLM_RESPONSES")

    # Performance Settings
    worker_processes: int = Field(4, env="WORKER_PROCESSES")
    memory_limit_mb: int = Field(512, env="MEMORY_LIMIT_MB")
    enable_caching: bool = Field(True, env="ENABLE_CACHING")
    cache_dir: Path = Field(Path("./.cache"), env="CACHE_DIR")
    cache_expiration_hours: int = Field(24, env="CACHE_EXPIRATION_HOURS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields from .env
    }

    @field_validator("supported_extensions")
    @classmethod
    def parse_extensions(cls, v):
        """Parse comma-separated extensions string."""
        if isinstance(v, str):
            return v  # Keep as string, parse when needed
        return v

    def get_supported_extensions(self) -> list[str]:
        """Get supported extensions as a list."""
        return [ext.strip() for ext in self.supported_extensions.split(",")]

    @field_validator("temp_dir", "output_dir", "cache_dir", mode="before")
    @classmethod
    def parse_path(cls, v):
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        """Validate model format."""
        if not v or "/" not in v:
            raise ValueError("Model must be in format 'provider/model-name'")
        return v

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


# Global settings instance
settings = Settings()
