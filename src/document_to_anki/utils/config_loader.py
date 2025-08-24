"""
Configuration loader utility for external YAML files.

This module provides utilities to load and validate configuration
from external YAML files, making the application more maintainable
and allowing for environment-specific configurations.
"""

from pathlib import Path
from typing import Any

import yaml
from loguru import logger


class ConfigLoader:
    """Load and manage external YAML configurations."""

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize the config loader.

        Args:
            config_dir: Directory containing config files (defaults to project root/configs)
        """
        if config_dir is None:
            # Default to configs directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = project_root / "configs"

        self.config_dir = Path(config_dir)
        self._cache: dict[str, Any] = {}

    def load_config(self, config_name: str, use_cache: bool = True) -> dict[str, Any]:
        """
        Load a configuration file.

        Args:
            config_name: Name of the config file (without .yml extension)
            use_cache: Whether to use cached version if available

        Returns:
            Dictionary containing the configuration data

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if use_cache and config_name in self._cache:
            cached_config: dict[str, Any] = self._cache[config_name]
            return cached_config

        config_path = self.config_dir / f"{config_name}.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data: dict[str, Any] = yaml.safe_load(f) or {}

            if use_cache:
                self._cache[config_name] = config_data

            logger.debug(f"Loaded configuration: {config_name}")
            return config_data

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config {config_name}: {e}")
            raise

    def get_models_config(self) -> dict[str, Any]:
        """Get the models configuration."""
        config: dict[str, Any] = self.load_config("models")
        return config

    def get_languages_config(self) -> dict[str, Any]:
        """Get the languages configuration."""
        config: dict[str, Any] = self.load_config("languages")
        return config

    def get_file_formats_config(self) -> dict[str, Any]:
        """Get the file formats configuration."""
        config: dict[str, Any] = self.load_config("file-formats")
        return config

    def get_supported_models(self) -> list[str]:
        """Get list of all supported model names."""
        models_config = self.get_models_config()
        supported_models = []

        for provider_models in models_config.get("models", {}).values():
            for model in provider_models:
                supported_models.append(model["name"])

        return supported_models

    def get_supported_languages(self) -> list[str]:
        """Get list of all supported language names and codes."""
        languages_config = self.get_languages_config()
        supported_languages = []

        for lang_data in languages_config.get("languages", {}).values():
            supported_languages.append(lang_data["name"].lower())
            supported_languages.append(lang_data["code"].lower())
            supported_languages.extend([alias.lower() for alias in lang_data.get("aliases", [])])

        return list(set(supported_languages))  # Remove duplicates

    def get_supported_file_extensions(self) -> list[str]:
        """Get list of all supported file extensions."""
        formats_config = self.get_file_formats_config()
        extensions = []

        for format_data in formats_config.get("formats", {}).values():
            extensions.extend(format_data.get("extensions", []))

        return extensions

    def get_model_info(self, model_name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific model.

        Args:
            model_name: Name of the model to look up

        Returns:
            Model information dictionary or None if not found
        """
        models_config = self.get_models_config()

        for provider_models in models_config.get("models", {}).values():
            for model in provider_models:
                if model["name"] == model_name:
                    model_info: dict[str, Any] = model
                    return model_info

        return None

    def get_language_info(self, language_input: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific language.

        Args:
            language_input: Language name, code, or alias

        Returns:
            Language information dictionary or None if not found
        """
        languages_config = self.get_languages_config()
        language_input_lower = language_input.lower()

        for lang_data in languages_config.get("languages", {}).values():
            # Check name, code, and aliases
            if (
                lang_data["name"].lower() == language_input_lower
                or lang_data["code"].lower() == language_input_lower
                or language_input_lower in [alias.lower() for alias in lang_data.get("aliases", [])]
            ):
                language_info: dict[str, Any] = lang_data
                return language_info

        return None

    def validate_model(self, model_name: str) -> bool:
        """Check if a model is supported."""
        return model_name in self.get_supported_models()

    def validate_language(self, language: str) -> bool:
        """Check if a language is supported."""
        return language.lower() in self.get_supported_languages()

    def validate_file_extension(self, extension: str) -> bool:
        """Check if a file extension is supported."""
        if not extension.startswith("."):
            extension = f".{extension}"
        return extension.lower() in [ext.lower() for ext in self.get_supported_file_extensions()]

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()
        logger.debug("Configuration cache cleared")


# Global instance for easy access
config_loader = ConfigLoader()


def load_external_config(config_name: str) -> dict[str, Any]:
    """
    Convenience function to load a configuration file.

    Args:
        config_name: Name of the config file (without .yml extension)

    Returns:
        Dictionary containing the configuration data
    """
    return config_loader.load_config(config_name)


# Example usage functions
def get_default_model() -> str:
    """Get the default model from configuration."""
    models_config = config_loader.get_models_config()

    # Find the default model
    for provider_models in models_config.get("models", {}).values():
        for model in provider_models:
            if model.get("default", False):
                model_name: str = model["name"]
                return model_name

    # Fallback to preferences
    preferences = models_config.get("preferences", {})
    fallback_model: str = preferences.get("fallback_model", "gemini/gemini-2.5-flash")
    return fallback_model


def get_default_language() -> str:
    """Get the default language from configuration."""
    languages_config = config_loader.get_languages_config()

    # Find the default language
    for lang_data in languages_config.get("languages", {}).values():
        if lang_data.get("default", False):
            language_name: str = lang_data["name"]
            return language_name

    # Fallback to settings
    settings = languages_config.get("settings", {})
    default_language: str = settings.get("default_language", "English")
    return default_language


if __name__ == "__main__":
    # Example usage
    loader = ConfigLoader()

    print("Supported models:", loader.get_supported_models())
    print("Supported languages:", loader.get_supported_languages())
    print("Supported file extensions:", loader.get_supported_file_extensions())

    print("Default model:", get_default_model())
    print("Default language:", get_default_language())

    # Test model lookup
    model_info = loader.get_model_info("gemini/gemini-2.5-flash")
    if model_info:
        print(f"Model info: {model_info['description']}")

    # Test language lookup
    lang_info = loader.get_language_info("fr")
    if lang_info:
        print(f"Language info: {lang_info['name']} ({lang_info['code']})")
