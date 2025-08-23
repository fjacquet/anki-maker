# Configuration Guide

This guide covers all configuration options for Document to Anki CLI.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [API Configuration](#api-configuration)
- [Web Interface Configuration](#web-interface-configuration)
- [Logging Configuration](#logging-configuration)
- [Performance Tuning](#performance-tuning)
- [Security Configuration](#security-configuration)

## Environment Variables

### Required Configuration

#### GEMINI_API_KEY
**Required**: Yes  
**Description**: Your Google Gemini API key for AI-powered flashcard generation  
**Example**: `GEMINI_API_KEY=AIzaSyDNDotML-zAnf9KXwcIdwiarwdgPCn8qmc`

**How to get an API key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your configuration

### Optional Configuration

#### LOG_LEVEL
**Default**: `INFO`  
**Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`  
**Description**: Controls the verbosity of application logging  
**Example**: `LOG_LEVEL=DEBUG`

#### LOGURU_LEVEL
**Default**: `INFO`  
**Options**: `TRACE`, `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`, `CRITICAL`  
**Description**: Controls loguru-specific logging levels  
**Example**: `LOGURU_LEVEL=DEBUG`

#### MODEL
**Default**: `gemini/gemini-2.5-flash`  
**Options**: Any litellm-supported model  
**Description**: The LLM model to use for flashcard generation  
**Examples**: 
- `MODEL=gemini/gemini-2.5-flash` (default)
- `MODEL=gemini/gemini-2.5-pro`
- `MODEL=openai/gpt-4o`
- `MODEL=openai/gpt-3.5-turbo`

#### LITELLM_TIMEOUT
**Default**: `300`  
**Description**: Request timeout in seconds for LLM API calls  
**Example**: `LITELLM_TIMEOUT=600`

#### WEB_HOST
**Default**: `127.0.0.1`  
**Description**: Host address for the web interface  
**Examples**:
- `WEB_HOST=0.0.0.0` (listen on all interfaces)
- `WEB_HOST=localhost` (local only)

#### WEB_PORT
**Default**: `8000`  
**Description**: Port number for the web interface  
**Example**: `WEB_PORT=8080`

### Advanced LLM Configuration

#### GEMINI_TEMPERATURE
**Default**: `0.3`  
**Range**: `0.0` to `1.0`  
**Description**: Controls randomness in LLM responses (lower = more consistent)  
**Example**: `GEMINI_TEMPERATURE=0.2`

#### GEMINI_MAX_TOKENS
**Default**: `20000`  
**Description**: Maximum tokens in LLM responses  
**Example**: `GEMINI_MAX_TOKENS=30000`

#### MAX_RETRIES
**Default**: `3`  
**Description**: Number of retry attempts for failed API calls  
**Example**: `MAX_RETRIES=5`

#### RETRY_DELAY
**Default**: `1.0`  
**Description**: Base delay in seconds for exponential backoff  
**Example**: `RETRY_DELAY=2.0`

## Configuration Files

### .env File

Create a `.env` file in your project root:

```bash
# Document to Anki CLI Configuration

# Required: Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Logging Configuration
LOG_LEVEL=INFO
LOGURU_LEVEL=INFO

# Optional: LLM Configuration
MODEL=gemini/gemini-2.5-flash
LITELLM_TIMEOUT=300
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_TOKENS=20000

# Optional: Web Interface Configuration
WEB_HOST=127.0.0.1
WEB_PORT=8000

# Optional: Performance Configuration
MAX_RETRIES=3
RETRY_DELAY=1.0
MAX_FILE_SIZE=52428800  # 50MB in bytes
MAX_FILES_COUNT=100

# Optional: Security Configuration
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### System Environment Variables

You can also set configuration through system environment variables:

```bash
# Linux/macOS
export GEMINI_API_KEY="your-api-key"
export LOG_LEVEL="DEBUG"

# Windows
set GEMINI_API_KEY=your-api-key
set LOG_LEVEL=DEBUG

# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key"
$env:LOG_LEVEL="DEBUG"
```

### Configuration Priority

Configuration is loaded in this order (later sources override earlier ones):

1. Default values in the code
2. System environment variables
3. `.env` file in the project root
4. Command-line arguments (where applicable)

## API Configuration

### Gemini API Setup

1. **Create Google Cloud Project** (if needed)
   - Visit [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one

2. **Enable Gemini API**
   - Go to APIs & Services → Library
   - Search for "Gemini API" or "Generative AI"
   - Enable the API

3. **Create API Key**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "API Key"
   - Copy the generated key

4. **Set Usage Limits** (recommended)
   - Go to APIs & Services → Quotas
   - Set daily/monthly limits to control costs

### API Key Security

**Best Practices:**
- Never commit API keys to version control
- Use environment variables or secure secret management
- Rotate keys regularly
- Set usage quotas and alerts
- Monitor API usage for unexpected spikes

**Secure Storage Options:**
```bash
# Option 1: .env file (add to .gitignore)
echo "GEMINI_API_KEY=your-key" >> .env
echo ".env" >> .gitignore

# Option 2: System keyring (macOS)
security add-generic-password -a "document-to-anki" -s "gemini-api" -w "your-key"

# Option 3: Environment variable in shell profile
echo 'export GEMINI_API_KEY="your-key"' >> ~/.bashrc
```

### Rate Limiting Configuration

```bash
# Configure rate limiting to avoid API quota issues
RATE_LIMIT_REQUESTS=60  # Requests per minute
RATE_LIMIT_TOKENS=100000  # Tokens per minute
RATE_LIMIT_DELAY=1.0  # Minimum delay between requests
```

## Web Interface Configuration

### Basic Web Server Settings

```bash
# Server configuration
WEB_HOST=0.0.0.0  # Listen on all interfaces
WEB_PORT=8000     # Port number
WEB_WORKERS=1     # Number of worker processes

# Session configuration
SESSION_TIMEOUT=3600  # 1 hour in seconds
SESSION_CLEANUP_INTERVAL=600  # 10 minutes

# File upload limits
MAX_UPLOAD_SIZE=52428800  # 50MB
MAX_FILES_PER_UPLOAD=10
ALLOWED_EXTENSIONS=.pdf,.docx,.txt,.md,.zip
```

### CORS Configuration

```bash
# Cross-Origin Resource Sharing settings
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE"]
CORS_ALLOW_HEADERS=["*"]
```

### Security Headers

```bash
# Security configuration
SECURITY_HEADERS_ENABLED=true
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
FRAME_OPTIONS=DENY
CONTENT_TYPE_OPTIONS=nosniff
```

### SSL/TLS Configuration

For production deployment with HTTPS:

```bash
# SSL configuration
SSL_ENABLED=true
SSL_CERT_PATH=/path/to/certificate.pem
SSL_KEY_PATH=/path/to/private-key.pem
SSL_CA_CERTS=/path/to/ca-bundle.pem

# Redirect HTTP to HTTPS
FORCE_HTTPS=true
```

## Logging Configuration

### Log Levels

```bash
# Application logging
LOG_LEVEL=INFO          # Application-wide log level
LOGURU_LEVEL=INFO       # Loguru-specific log level
LITELLM_LOG_LEVEL=ERROR # LLM client log level

# Component-specific logging
DOCUMENT_PROCESSOR_LOG_LEVEL=INFO
FLASHCARD_GENERATOR_LOG_LEVEL=INFO
WEB_APP_LOG_LEVEL=INFO
```

### Log Output Configuration

```bash
# Log output destinations
LOG_TO_CONSOLE=true
LOG_TO_FILE=false
LOG_FILE_PATH=logs/document-to-anki.log
LOG_FILE_MAX_SIZE=10MB
LOG_FILE_BACKUP_COUNT=5

# Log formatting
LOG_FORMAT="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
LOG_COLORIZE=true
```

### Structured Logging

```bash
# JSON logging for production
LOG_JSON_FORMAT=false
LOG_INCLUDE_EXTRA=true

# Performance logging
LOG_PERFORMANCE_METRICS=false
LOG_API_CALLS=false
LOG_FILE_OPERATIONS=false
```

## Performance Tuning

### Memory Configuration

```bash
# Memory limits
MAX_MEMORY_USAGE=2GB
MEMORY_WARNING_THRESHOLD=1.5GB

# Text processing
MAX_TEXT_CHUNK_SIZE=4000  # Tokens per chunk
TEXT_OVERLAP_SIZE=200     # Overlap between chunks

# Concurrent processing
MAX_CONCURRENT_REQUESTS=5
MAX_CONCURRENT_FILES=3
```

### Caching Configuration

```bash
# Response caching
CACHE_ENABLED=true
CACHE_TTL=3600           # 1 hour
CACHE_MAX_SIZE=100MB
CACHE_BACKEND=memory     # memory, redis, file

# File processing cache
CACHE_EXTRACTED_TEXT=true
CACHE_GENERATED_FLASHCARDS=false
```

### Database Configuration (if using persistent storage)

```bash
# Database settings
DATABASE_URL=sqlite:///flashcards.db
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
```

## Security Configuration

### File Upload Security

```bash
# File validation
VALIDATE_FILE_SIGNATURES=true
SCAN_FOR_MALWARE=false
QUARANTINE_SUSPICIOUS_FILES=true

# Path security
ALLOW_PATH_TRAVERSAL=false
SANITIZE_FILENAMES=true
MAX_PATH_LENGTH=255
```

### API Security

```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10

# Authentication (if implemented)
AUTH_ENABLED=false
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRATION_TIME=3600

# API key validation
VALIDATE_API_KEYS=true
API_KEY_HEADER=X-API-Key
```

### Content Security

```bash
# Content filtering
FILTER_SENSITIVE_CONTENT=false
CONTENT_SAFETY_LEVEL=medium  # low, medium, high
BLOCK_PERSONAL_INFO=true

# Output sanitization
SANITIZE_OUTPUT=true
ESCAPE_HTML=true
VALIDATE_CSV_OUTPUT=true
```

## Model Configuration

### Supported Models

The application supports multiple LLM providers through configurable model selection:

#### Gemini Models (Google)
- `gemini/gemini-2.5-flash` (default) - Fast and efficient
- `gemini/gemini-2.5-pro` - More capable, higher quality
- **Required**: `GEMINI_API_KEY` environment variable

#### OpenAI Models
- `openai/gpt-4o` - Latest GPT-4 model
- `openai/gpt-4` - Standard GPT-4
- `openai/gpt-3.5-turbo` - Faster, lower cost
- `openai/gpt-4.1`, `openai/gpt-4.1-mini`, `openai/gpt-4.1-nano` - Variants
- `openai/gpt-5`, `openai/gpt-5-mini`, `openai/gpt-5-nano` - Future models
- **Required**: `OPENAI_API_KEY` environment variable

### Model Selection

Set the `MODEL` environment variable to choose your preferred model:

```bash
# Use Gemini (default)
MODEL=gemini/gemini-2.5-flash

# Use OpenAI GPT-4
MODEL=openai/gpt-4o

# Use OpenAI GPT-3.5 (faster, cheaper)
MODEL=openai/gpt-3.5-turbo
```

### API Key Requirements

Each model provider requires its corresponding API key:

```bash
# For Gemini models
GEMINI_API_KEY=your-gemini-api-key

# For OpenAI models  
OPENAI_API_KEY=your-openai-api-key

# You can have both keys configured and switch models as needed
```

### Model Configuration Validation

The application validates model configuration on startup:
- Checks if the specified model is supported
- Verifies the required API key is available
- Provides clear error messages for configuration issues

## Configuration Validation

### Integration Test

The project includes a comprehensive integration test to validate that the FlashcardGenerator properly uses ModelConfig:

```bash
# Run the integration test
python test_integration_check.py
```

This test validates:
- Default model configuration with valid API keys
- Custom model selection with appropriate API keys  
- Error handling for invalid models
- Error handling for missing API keys
- ModelConfig method functionality

### Validation Scripts

The project includes multiple validation scripts to test your configuration:

#### Integration Test for Model Configuration
```bash
# Run comprehensive model configuration test
python test_integration_check.py
```

This validates FlashcardGenerator integration with ModelConfig and tests all supported models and API key combinations.

#### Web App Startup Validation Test
```bash
# Run web application startup validation
python test_startup_validation.py
```

This validates that the web application properly handles configuration validation during startup.

#### Custom Validation Script

Create a script to validate your configuration:

```python
#!/usr/bin/env python3
"""Configuration validation script."""

import os
import sys
from pathlib import Path

def validate_required_config():
    """Validate required configuration."""
    from document_to_anki.config import ModelConfig, ConfigurationError
    
    try:
        # This validates both model support and API key availability
        model = ModelConfig.validate_and_get_model()
        print(f"✅ Model configuration valid: {model}")
        return True
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return False

def validate_optional_config():
    """Validate optional configuration."""
    from document_to_anki.config import ModelConfig
    
    config_checks = {
        'LOG_LEVEL': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        'WEB_PORT': lambda x: x.isdigit() and 1 <= int(x) <= 65535,
    }
    
    # Check MODEL separately using ModelConfig
    model = os.getenv('MODEL', ModelConfig.DEFAULT_MODEL)
    if model not in ModelConfig.get_supported_models():
        print(f"⚠️ Unsupported model: {model}")
        print(f"   Supported models: {', '.join(ModelConfig.get_supported_models())}")
    else:
        print(f"✅ Model is supported: {model}")
    
    for var, valid_values in config_checks.items():
        value = os.getenv(var)
        if value:
            if isinstance(valid_values, list) and value not in valid_values:
                print(f"⚠️ Invalid value for {var}: {value}")
                print(f"   Valid values: {', '.join(valid_values)}")
            elif callable(valid_values) and not valid_values(value):
                print(f"⚠️ Invalid value for {var}: {value}")

def test_api_connection():
    """Test API connection."""
    try:
        from document_to_anki.core.llm_client import LLMClient
        from document_to_anki.config import ModelConfig
        
        # Get the configured model
        model = ModelConfig.validate_and_get_model()
        print(f"Testing API connection with model: {model}")
        
        client = LLMClient()
        result = client.generate_flashcards_from_text_sync("Test content for API validation.")
        
        if result:
            print(f"✅ API connection successful - generated {len(result)} test flashcards")
            return True
        else:
            print("❌ API connection failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Configuration Validation")
    print("=" * 30)
    
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    else:
        print("ℹ️ No .env file found")
    
    # Validate configuration
    valid = validate_required_config()
    validate_optional_config()
    
    if valid:
        test_api_connection()
    
    print("\n🎉 Validation complete!")
```

### Environment Template

Create a template for new installations:

```bash
# .env.template
# Copy this file to .env and fill in your values

# Required: API Keys (at least one required based on model choice)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Model Selection (uncomment to customize)
# MODEL=gemini/gemini-2.5-flash  # Default
# MODEL=gemini/gemini-2.5-pro    # More capable Gemini
# MODEL=openai/gpt-4o           # Latest OpenAI
# MODEL=openai/gpt-3.5-turbo    # Faster OpenAI

# Optional: Logging (uncomment to customize)
# LOG_LEVEL=INFO
# LOGURU_LEVEL=INFO

# Optional: LLM Configuration (uncomment to customize)
# LITELLM_TIMEOUT=300

# Optional: Web Interface (uncomment to customize)
# WEB_HOST=127.0.0.1
# WEB_PORT=8000

# Optional: Performance (uncomment to customize)
# MAX_RETRIES=3
# RETRY_DELAY=1.0

# Optional: Security (uncomment to customize)
# CORS_ORIGINS=["http://localhost:3000"]
```

## Development Setup

### Installing Development Dependencies

For development work, use the enhanced installation command that includes all optional dependencies:

```bash
# Install all development dependencies (recommended for contributors)
make install-dev

# Or directly with uv
uv sync --all-extras
```

This installs:
- Testing frameworks (pytest, pytest-cov, pytest-mock)
- Code quality tools (ruff, mypy, bandit, safety)
- Development utilities (pre-commit, watchdog)

### Development Workflow

```bash
# 1. Set up development environment
make install-dev

# 2. Run quality checks (includes automatic code formatting)
make quality

# 3. Run tests
make test

# 4. Run specific test categories
make test-integration
```

**Important**: The `make quality` command now automatically formats your code files using `ruff format`. This ensures consistent code style but will modify your files. The change improves development workflow by automatically applying formatting fixes rather than just reporting formatting issues.

This comprehensive configuration guide covers all aspects of setting up and tuning Document to Anki CLI for your specific needs.