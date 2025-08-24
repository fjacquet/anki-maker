# External Configuration Files

This directory contains externalized YAML configuration files that make the Document to Anki CLI more maintainable and customizable.

## Configuration Files

### Application Configurations

#### `models.yml`
Defines supported AI models and their configurations:
- **Gemini models**: Google's Gemini Pro and Flash models
- **OpenAI models**: GPT-4, GPT-3.5-turbo variants
- **Model metadata**: API keys, token limits, cost tiers
- **Default preferences**: Fallback models, retry settings

#### `languages.yml`
Defines supported languages for flashcard generation:
- **Language definitions**: Name, code, aliases
- **Validation rules**: Character limits, allowed characters
- **Default settings**: Fallback language configuration

#### `file-formats.yml`
Defines supported document formats:
- **Format specifications**: Extensions, MIME types, processors
- **Processing limits**: File size limits, batch settings
- **Feature flags**: Available processing features per format

### Docker Configurations

#### `docker/development.yml`
Development-specific Docker Compose configuration:
- **Hot reload**: Automatic code reloading
- **Debug settings**: Verbose logging, development mode
- **Volume mounts**: Source code mounting for live editing

#### `docker/production.yml`
Production-optimized Docker Compose configuration:
- **Resource limits**: Memory and CPU constraints
- **Security settings**: Minimal attack surface
- **Optional services**: Redis caching, Nginx proxy

### GitHub Actions Configurations

#### `.github/workflows/configs/python-setup.yml`
Reusable Python setup action:
- **Python installation**: Version-specific setup
- **Dependency management**: uv installation and package setup
- **Configurable options**: Development vs production dependencies

#### `.github/workflows/configs/test-matrix.yml`
Test matrix configuration:
- **Python versions**: Supported Python versions for testing
- **Operating systems**: Target platforms
- **Environment variables**: Test-specific settings

#### `.github/workflows/configs/docker-config.yml`
Docker build configuration:
- **Multi-platform builds**: AMD64 and ARM64 support
- **Metadata generation**: Tags, labels, build args
- **Cache optimization**: GitHub Actions cache settings

## Usage Examples

### Loading Configurations in Python

```python
from document_to_anki.utils.config_loader import ConfigLoader

# Initialize config loader
loader = ConfigLoader()

# Load specific configurations
models_config = loader.get_models_config()
languages_config = loader.get_languages_config()
formats_config = loader.get_file_formats_config()

# Get supported items
supported_models = loader.get_supported_models()
supported_languages = loader.get_supported_languages()
supported_extensions = loader.get_supported_file_extensions()

# Validate inputs
is_valid_model = loader.validate_model("gemini/gemini-2.5-flash")
is_valid_language = loader.validate_language("french")
is_valid_extension = loader.validate_file_extension(".pdf")

# Get detailed information
model_info = loader.get_model_info("gemini/gemini-2.5-flash")
language_info = loader.get_language_info("fr")
```

### Using Docker Configurations

```bash
# Development environment
docker-compose -f docker-compose.yml -f configs/docker/development.yml up

# Production environment  
docker-compose -f docker-compose.yml -f configs/docker/production.yml up -d

# Using Makefile shortcuts
make docker-dev    # Development
make docker-prod   # Production
make docker-down   # Stop all services
```

### Using GitHub Actions Configurations

```yaml
# In your workflow file
steps:
  - name: Setup Python and Dependencies
    uses: ./.github/workflows/configs/python-setup.yml
    with:
      python-version: '3.12'
      install-dev: 'true'
```

## Configuration Schema

### Models Configuration Schema

```yaml
models:
  <provider>:
    - name: string              # Model identifier
      description: string       # Human-readable description
      api_key_env: string      # Environment variable for API key
      default: boolean         # Whether this is the default model
      max_tokens: integer      # Maximum token limit
      cost_tier: string        # Cost category (low/medium/high)

preferences:
  default_provider: string     # Preferred provider
  fallback_model: string      # Fallback model name
  max_retries: integer        # Maximum retry attempts
  timeout_seconds: integer    # Request timeout
```

### Languages Configuration Schema

```yaml
languages:
  <language_key>:
    code: string               # ISO language code
    name: string               # Full language name
    aliases: [string]          # Alternative names/codes
    default: boolean           # Whether this is default

settings:
  default_language: string     # Default language name
  fallback_language: string   # Fallback language
  case_sensitive: boolean     # Case sensitivity for matching

validation:
  min_name_length: integer    # Minimum name length
  max_name_length: integer    # Maximum name length
  allowed_characters: string  # Allowed character set
```

### File Formats Configuration Schema

```yaml
formats:
  <format_key>:
    extensions: [string]       # File extensions
    mime_types: [string]       # MIME type identifiers
    description: string        # Format description
    max_size_mb: integer      # Maximum file size
    processor: string         # Processing library
    features: [string]        # Available features

processing:
  max_total_size_mb: integer  # Total batch size limit
  max_files_per_batch: integer # File count limit
  supported_encodings: [string] # Text encodings

validation:
  check_file_signature: boolean # Verify file signatures
  verify_mime_type: boolean     # Check MIME types
  scan_for_malware: boolean     # Malware scanning
```

## Benefits of External Configuration

### 1. **Maintainability**
- **Centralized settings**: All configuration in one place
- **Easy updates**: Modify settings without code changes
- **Version control**: Track configuration changes separately

### 2. **Flexibility**
- **Environment-specific**: Different configs for dev/prod
- **Feature flags**: Enable/disable features via config
- **Easy customization**: Users can modify behavior

### 3. **Reusability**
- **Shared configurations**: Reuse across different components
- **Template-based**: Create new environments from templates
- **Modular design**: Mix and match configuration files

### 4. **Validation**
- **Schema validation**: Ensure configuration correctness
- **Type checking**: Validate data types and formats
- **Error prevention**: Catch configuration errors early

## Best Practices

### 1. **Configuration Management**
- Keep configurations in version control
- Use meaningful names and descriptions
- Document all configuration options
- Validate configurations on load

### 2. **Security**
- Never store secrets in configuration files
- Use environment variables for sensitive data
- Implement proper access controls
- Regular security reviews

### 3. **Performance**
- Cache frequently accessed configurations
- Lazy load large configurations
- Monitor configuration load times
- Optimize for common use cases

### 4. **Testing**
- Test with different configuration combinations
- Validate configuration schemas
- Test configuration loading and error handling
- Include configuration tests in CI/CD

## Migration Guide

If you're migrating from hardcoded configurations:

1. **Identify hardcoded values** in your codebase
2. **Create appropriate YAML files** using the schemas above
3. **Update code** to use `ConfigLoader` instead of hardcoded values
4. **Test thoroughly** with different configuration combinations
5. **Update documentation** to reflect new configuration options

## Contributing

When adding new configuration options:

1. **Update the appropriate YAML file** with new settings
2. **Update the schema documentation** in this README
3. **Add validation logic** in `config_loader.py` if needed
4. **Update tests** to cover new configuration options
5. **Document the changes** in the changelog

For more information about the configuration system, see the main [API documentation](../docs/API.md) and [configuration guide](../docs/CONFIGURATION.md).