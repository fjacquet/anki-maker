# Test Fixtures

This directory contains external test data and configurations for the Document to Anki CLI test suite.

## Directory Structure

```
tests/fixtures/
├── sample_documents/          # Test document files
├── expected_outputs/          # Expected test outputs
├── mock_llm_responses.yml     # Mock LLM response configurations
├── test_config.yml           # Test configuration settings
├── test_data_loader.py       # Utility for loading test data
└── language_test_data.yaml   # Language-specific test data
```

## Sample Documents

### `sample_documents/`

Contains various document types used for testing:

- **`python_basics.txt`** - Text file about Python programming
- **`machine_learning.md`** - Markdown file about ML concepts
- **`mixed_content.txt`** - Content for testing different card types
- **`large_document.txt`** - Template for large document testing
- **`performance_test.txt`** - Template for performance testing

These files are used by the `test_end_to_end.py` tests to create consistent test scenarios without hardcoding content in the test files.

## Configuration Files

### `mock_llm_responses.yml`

Defines mock responses for different document types:

```yaml
responses:
  python_programming:
    trigger_keywords: ["Python", "programming"]
    flashcards:
      - question: "What is Python?"
        answer: "A high-level, interpreted programming language"
        card_type: "qa"
```

**Features:**
- Keyword-based response matching
- Different card types (Q&A, cloze deletion)
- Error simulation scenarios
- Configurable matching strategies

### `test_config.yml`

Contains test configuration settings:

```yaml
timeouts:
  single_file_workflow: 60
  performance_workflow: 60

performance:
  document_processing:
    max_time_seconds: 5
    max_memory_mb: 50
```

**Features:**
- Test timeout configurations
- Performance expectations
- Document size settings
- Memory usage limits
- Validation rules

## Test Data Loader

### `test_data_loader.py`

Utility class for loading external test data:

```python
from tests.fixtures.test_data_loader import test_data_loader

# Load document content
content = test_data_loader.load_document_content("python_basics.txt")

# Create temporary test files
temp_file = test_data_loader.create_temp_document(temp_dir, "python_basics.txt")

# Get mock LLM responses
mock_function = test_data_loader.create_mock_llm_function()

# Load configuration
config = test_data_loader.get_test_config()
```

**Features:**
- Document content loading
- Temporary file creation
- Mock response generation
- Configuration management
- Caching for performance

## Usage in Tests

### Loading External Documents

Instead of hardcoding document content in tests:

```python
# Old approach (hardcoded)
def test_example(self, temp_dir):
    content = """
    Long hardcoded content here...
    """
    file_path = temp_dir / "test.txt"
    file_path.write_text(content)

# New approach (external)
def test_example(self, temp_dir):
    from tests.fixtures.test_data_loader import test_data_loader
    file_path = test_data_loader.create_temp_document(temp_dir, "python_basics.txt")
```

### Using Mock Responses

Instead of defining mock responses in each test:

```python
# Old approach (hardcoded)
@pytest.fixture
def mock_responses(self, mocker):
    responses = [
        {"question": "What is Python?", "answer": "...", "card_type": "qa"}
    ]
    mocker.patch("...", return_value=responses)

# New approach (external)
@pytest.fixture
def mock_responses(self, mocker):
    from tests.fixtures.test_data_loader import test_data_loader
    mock_function = test_data_loader.create_mock_llm_function()
    mocker.patch("...", side_effect=mock_function)
```

### Using Configuration

Instead of hardcoding test parameters:

```python
# Old approach (hardcoded)
def test_performance(self):
    max_time = 5.0  # Hardcoded
    assert processing_time < max_time

# New approach (external)
def test_performance(self):
    from tests.fixtures.test_data_loader import test_data_loader
    perf_config = test_data_loader.get_performance_expectations("document_processing")
    max_time = perf_config.get("max_time_seconds", 5.0)
    assert processing_time < max_time
```

## Benefits

### 1. **Maintainability**
- Test data centralized in external files
- Easy to modify without touching test code
- Consistent test scenarios across different tests

### 2. **Reusability**
- Same documents can be used by multiple tests
- Mock responses shared across test suites
- Configuration templates for different scenarios

### 3. **Readability**
- Tests focus on logic, not data setup
- Clear separation between test logic and test data
- Easier to understand test intentions

### 4. **Performance**
- Reduced test file sizes
- Caching of frequently used data
- Faster test execution with optimized data loading

### 5. **Flexibility**
- Easy to add new test scenarios
- Configurable test parameters
- Environment-specific test settings

## Adding New Test Data

### 1. **New Document Types**

To add a new document type:

1. Create the document file in `sample_documents/`
2. Add corresponding mock responses in `mock_llm_responses.yml`
3. Update test configuration in `test_config.yml` if needed

### 2. **New Mock Responses**

To add new mock response scenarios:

1. Add new response type in `mock_llm_responses.yml`
2. Define trigger keywords and flashcard responses
3. Use in tests via `test_data_loader.create_mock_llm_function()`

### 3. **New Configuration Options**

To add new test configuration:

1. Add settings to appropriate section in `test_config.yml`
2. Update `test_data_loader.py` with getter methods if needed
3. Use in tests via `test_data_loader.get_test_config()`

## Best Practices

### 1. **Document Naming**
- Use descriptive names that indicate content type
- Include file extension for clarity
- Keep names consistent with test scenarios

### 2. **Mock Response Design**
- Use realistic flashcard content
- Include both valid and invalid examples for testing
- Match trigger keywords to document content

### 3. **Configuration Management**
- Group related settings together
- Use reasonable default values
- Document configuration options

### 4. **Performance Considerations**
- Keep document files reasonably sized
- Use caching for frequently accessed data
- Avoid loading unnecessary data in tests

## Migration from Hardcoded Data

If migrating existing tests:

1. **Extract hardcoded content** to external files
2. **Replace inline data** with loader calls
3. **Update mock fixtures** to use external configurations
4. **Test thoroughly** to ensure behavior is unchanged
5. **Update documentation** to reflect new structure

This externalization makes the test suite much more maintainable and allows for easier test data management!