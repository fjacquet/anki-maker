---
inclusion: always
---

# Code Quality Standards

## Testing Principles

### Core Testing Rules
- Tests must focus on feature behavior, not implementation details
- External systems (LLM APIs, file system) must be mocked using `pytest-mock`
- Tests must be independent and not rely on execution order
- Tests must be repeatable with consistent results
- Tests must execute quickly (< 5 seconds for unit tests)
- Tests must be readable with clear naming and documentation
- Always use the latest package versions and modern testing patterns

### Test Organization
- Use descriptive test names: `test_should_generate_flashcards_when_valid_pdf_provided`
- Group related tests in classes with `Test` prefix
- Use pytest fixtures for common setup in `conftest.py`
- Mark tests appropriately: `@pytest.mark.integration`, `@pytest.mark.slow`

### Mocking Standards
- Mock external dependencies at the boundary (LLM client, file operations)
- Use `pytest-mock` instead of `unittest.mock` for consistency
- Mock return values should match real API responses
- Verify mock calls with `assert_called_with()` for critical interactions

## Code Style

### Python Conventions
- Follow PEP 8 with 110 character line limit
- Use type hints for all public methods and complex private methods
- Prefer explicit imports over wildcard imports
- Use descriptive variable names: `flashcard_count` not `fc`

### Error Handling
- Use custom exception classes for domain-specific errors
- Provide actionable error messages with context
- Log errors with appropriate levels (ERROR for failures, WARNING for recoverable issues)
- Handle edge cases gracefully with user-friendly messages

### Documentation
- Docstrings required for all public classes and methods
- Use Google-style docstrings with Args, Returns, and Raises sections
- Include usage examples in docstrings for complex functions
- Keep README and API documentation synchronized with code changes

## Architecture Patterns

### Dependency Management
- Use dependency injection for testability
- Keep external dependencies at module boundaries
- Use factory patterns for complex object creation
- Prefer composition over inheritance

### Configuration
- Use Pydantic models for configuration validation
- Support both environment variables and config files
- Provide sensible defaults for all optional settings
- Validate configuration at startup with clear error messages

### Async/Await Usage
- Use async/await for I/O operations (file reading, API calls)
- Avoid blocking operations in async contexts
- Use `asyncio.gather()` for concurrent operations
- Handle async exceptions properly with try/except blocks

## Performance Guidelines

### Memory Management
- Process large documents in chunks to avoid memory issues
- Use generators for large data sets
- Clean up temporary files and resources
- Monitor memory usage in tests for large file processing

### API Efficiency
- Batch API calls when possible to reduce latency
- Implement retry logic with exponential backoff
- Cache expensive operations when appropriate
- Use connection pooling for HTTP clients

## Security Practices

### Input Validation
- Validate all user inputs with Pydantic models
- Sanitize file paths to prevent directory traversal
- Limit file sizes and types for uploads
- Escape user content in web templates

### API Key Management
- Never log or expose API keys in error messages
- Use environment variables for sensitive configuration
- Validate API keys at startup
- Provide clear guidance for API key setup

## Development Workflow

### Pre-commit Checks
- Run `make quality` before committing changes
- Ensure all tests pass with `make test`
- Fix linting issues with `make lint-fix`
- Update documentation for public API changes

### Code Review Standards
- Review for security vulnerabilities and input validation
- Verify test coverage for new features
- Check for proper error handling and logging
- Ensure consistent code style and naming conventions