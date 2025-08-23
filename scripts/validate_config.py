#!/usr/bin/env python3
"""Configuration validation script for Document to Anki CLI."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv

    from document_to_anki.config import settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install dependencies: uv pip install -e .")
    sys.exit(1)


def validate_api_keys():
    """Validate API key configuration."""
    print("🔑 Validating API keys...")

    api_key = settings.get_api_key()
    if not api_key:
        print("❌ No API key found for the configured model")
        print(f"   Model: {settings.model}")
        print("   Please set GEMINI_API_KEY or OPENAI_API_KEY in your .env file")
        return False

    if len(api_key) < 10:
        print("⚠️  API key seems too short - please verify it's correct")
        return False

    print(f"✅ API key found for model: {settings.model}")
    return True


def validate_directories():
    """Validate directory configuration."""
    print("📁 Validating directories...")

    try:
        settings.ensure_directories()
        print(f"✅ Temp directory: {settings.temp_dir}")
        print(f"✅ Output directory: {settings.output_dir}")
        print(f"✅ Cache directory: {settings.cache_dir}")
        return True
    except Exception as e:
        print(f"❌ Directory validation failed: {e}")
        return False


def validate_model_config():
    """Validate model configuration."""
    print("🤖 Validating model configuration...")

    try:
        model = settings.model
        if "/" not in model:
            print(f"❌ Invalid model format: {model}")
            print("   Model should be in format 'provider/model-name'")
            return False

        provider, model_name = model.split("/", 1)
        supported_providers = ["gemini", "openai", "anthropic", "ollama"]

        if provider not in supported_providers:
            print(f"⚠️  Unknown provider: {provider}")
            print(f"   Supported providers: {supported_providers}")

        print(f"✅ Model configuration: {model}")
        return True
    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        return False


def validate_file_settings():
    """Validate file processing settings."""
    print("📄 Validating file settings...")

    try:
        print(f"✅ Max file size: {settings.max_file_size_mb} MB")
        print(f"✅ Supported extensions: {settings.supported_extensions}")
        print(f"✅ Max batch size: {settings.max_batch_size}")

        if settings.max_file_size_mb > 1000:
            print("⚠️  Very large file size limit - may cause memory issues")

        return True
    except Exception as e:
        print(f"❌ File settings validation failed: {e}")
        return False


def validate_performance_settings():
    """Validate performance settings."""
    print("⚡ Validating performance settings...")

    try:
        print(f"✅ Worker processes: {settings.worker_processes}")
        print(f"✅ Memory limit: {settings.memory_limit_mb} MB")
        print(f"✅ LLM timeout: {settings.llm_timeout}s")
        print(f"✅ Max retries: {settings.llm_max_retries}")

        if settings.worker_processes > os.cpu_count():
            print(f"⚠️  Worker processes ({settings.worker_processes}) > CPU cores ({os.cpu_count()})")

        return True
    except Exception as e:
        print(f"❌ Performance settings validation failed: {e}")
        return False


def test_imports():
    """Test that all required modules can be imported."""
    print("📦 Testing imports...")

    required_modules = [
        "click",
        "fastapi",
        "pydantic",
        "pandas",
        "numpy",
        "rich",
        "loguru",
        "litellm",
        "PyPDF2",
        "docx",
        "jinja2",
    ]

    failed_imports = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)

    if failed_imports:
        print(f"\n❌ Failed to import: {failed_imports}")
        print("Please install missing dependencies: uv pip install -e .")
        return False

    return True


def main():
    """Main validation function."""
    print("🔍 Document to Anki CLI - Configuration Validation")
    print("=" * 50)

    # Load environment variables
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from: {env_file}")
    else:
        print("⚠️  No .env file found - using default settings")

    print()

    # Run all validations
    validations = [
        test_imports,
        validate_api_keys,
        validate_model_config,
        validate_directories,
        validate_file_settings,
        validate_performance_settings,
    ]

    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append(False)
            print()

    # Summary
    print("📊 Validation Summary")
    print("-" * 20)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All validations passed ({passed}/{total})")
        print("🎉 Configuration is ready!")
        return 0
    else:
        print(f"❌ {total - passed} validation(s) failed ({passed}/{total})")
        print("🔧 Please fix the issues above before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
