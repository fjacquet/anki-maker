# Performance Tests

This directory contains performance and stress tests for the document-to-anki-cli project.

## Purpose

Performance tests are separated from the main test suite to:
- Keep regular test runs fast
- Allow focused performance testing
- Enable benchmarking and regression detection
- Support load testing and scalability validation

## Running Performance Tests

### Run all performance tests:
```bash
uv run pytest tests/performance/
```

### Run specific performance test file:
```bash
uv run pytest tests/performance/test_language_performance.py
```

### Run with verbose output:
```bash
uv run pytest tests/performance/ -v
```

### Run with timing information:
```bash
uv run pytest tests/performance/ --durations=10
```

## Test Categories

### Language Performance Tests (`test_language_performance.py`)
- Language validation and normalization performance
- Settings instantiation across different languages
- LLM client initialization performance
- Prompt template retrieval performance
- Flashcard generation performance by language
- Concurrent operations performance
- Memory usage validation
- Scalability testing

## Performance Benchmarks

The tests include performance benchmarks to detect regressions:
- Language validation: < 10ms per operation
- Settings instantiation: < 500ms per operation
- LLM client initialization: < 500ms per operation
- Prompt template retrieval: < 10ms per operation

## CI Integration

Performance tests can be run in CI with:
```bash
make test-performance  # If added to Makefile
```

Or manually:
```bash
uv run pytest tests/performance/ --tb=short
```

## Adding New Performance Tests

When adding new performance tests:
1. Follow the naming convention: `test_*_performance.py`
2. Use appropriate fixtures for mocking external dependencies
3. Set reasonable performance thresholds
4. Include memory usage validation where relevant
5. Test both sequential and concurrent scenarios
6. Document expected performance characteristics