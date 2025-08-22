"""
Shared pytest fixtures and configuration for integration tests.
"""

import tempfile
from pathlib import Path

import pytest

from src.document_to_anki.core.document_processor import DocumentProcessingResult
from src.document_to_anki.models.flashcard import Flashcard, ProcessingResult


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_text_file(temp_directory):
    """Create a sample text file for testing."""
    content = """
    Introduction to Python Programming
    
    Python is a high-level, interpreted programming language known for its simplicity and readability.
    It was created by Guido van Rossum and first released in 1991.
    
    Key Features:
    - Easy to learn and use
    - Interpreted language
    - Object-oriented programming support
    - Large standard library
    - Cross-platform compatibility
    
    Python is widely used in:
    - Web development
    - Data science and analytics
    - Artificial intelligence and machine learning
    - Automation and scripting
    - Scientific computing
    """
    
    file_path = temp_directory / "sample_python.txt"
    file_path.write_text(content.strip())
    return file_path


@pytest.fixture
def sample_markdown_file(temp_directory):
    """Create a sample markdown file for testing."""
    content = """
    # Data Science Fundamentals
    
    Data Science is an interdisciplinary field that uses scientific methods, processes,
    algorithms and systems to extract knowledge and insights from structured and unstructured data.
    
    ## Key Components
    
    ### Statistics and Mathematics
    - Descriptive statistics
    - Inferential statistics
    - Linear algebra
    - Calculus
    
    ### Programming Skills
    - Python or R programming
    - SQL for database queries
    - Data manipulation libraries (pandas, NumPy)
    
    ### Machine Learning
    - Supervised learning algorithms
    - Unsupervised learning techniques
    - Model evaluation and validation
    - Feature engineering
    
    ## Data Science Process
    
    1. **Problem Definition**: Understanding the business problem
    2. **Data Collection**: Gathering relevant data from various sources
    3. **Data Cleaning**: Preprocessing and cleaning the data
    4. **Exploratory Data Analysis**: Understanding data patterns
    5. **Model Building**: Creating predictive or descriptive models
    6. **Model Evaluation**: Testing model performance
    7. **Deployment**: Implementing the solution in production
    """
    
    file_path = temp_directory / "sample_datascience.md"
    file_path.write_text(content.strip())
    return file_path


@pytest.fixture
def sample_flashcards():
    """Create sample flashcard objects for testing."""
    return [
        Flashcard.create(
            question="What is Python?",
            answer="A high-level, interpreted programming language known for its simplicity and readability",
            card_type="qa",
            source_file="sample.txt"
        ),
        Flashcard.create(
            question="Who created Python?",
            answer="Guido van Rossum",
            card_type="qa",
            source_file="sample.txt"
        ),
        Flashcard.create(
            question="Python was first released in {{c1::1991}}",
            answer="1991",
            card_type="cloze",
            source_file="sample.txt"
        ),
        Flashcard.create(
            question="What is Data Science?",
            answer="An interdisciplinary field that uses scientific methods to extract knowledge from data",
            card_type="qa",
            source_file="datascience.md"
        ),
        Flashcard.create(
            question="Data Science uses {{c1::scientific methods}} to extract {{c2::knowledge}} from data",
            answer="scientific methods and knowledge",
            card_type="cloze",
            source_file="datascience.md"
        )
    ]


@pytest.fixture
def mock_document_processing_result():
    """Create a mock document processing result."""
    return DocumentProcessingResult(
        text_content="Sample processed text content for testing purposes.",
        source_files=["sample.txt", "datascience.md"],
        file_count=2,
        total_characters=50
    )


@pytest.fixture
def mock_flashcard_generation_result(sample_flashcards):
    """Create a mock flashcard generation result."""
    return ProcessingResult(
        flashcards=sample_flashcards,
        source_files=["sample.txt", "datascience.md"],
        processing_time=2.5,
        errors=[],
        warnings=[]
    )


@pytest.fixture
def mock_successful_llm_response():
    """Mock successful LLM response data."""
    return [
        {
            "question": "What is the main topic of this document?",
            "answer": "Programming and technology concepts",
            "card_type": "qa"
        },
        {
            "question": "The document discusses {{c1::programming}} concepts",
            "answer": "programming",
            "card_type": "cloze"
        },
        {
            "question": "What are the key benefits mentioned?",
            "answer": "Simplicity, readability, and ease of use",
            "card_type": "qa"
        }
    ]


@pytest.fixture
def mock_csv_export_summary():
    """Mock CSV export summary data."""
    return {
        "total_flashcards": 5,
        "exported_flashcards": 5,
        "skipped_invalid": 0,
        "qa_cards": 3,
        "cloze_cards": 2,
        "file_size_bytes": 350,
        "output_path": "test_output.csv",
        "source_files": ["sample.txt", "datascience.md"],
        "errors": []
    }


@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Automatically cleanup web app sessions after each test."""
    yield
    # Clean up any sessions created during tests
    from src.document_to_anki.web.app import sessions
    sessions.clear()


@pytest.fixture
def integration_test_marker():
    """Marker for integration tests."""
    return pytest.mark.integration


# Pytest configuration for integration tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "cli: mark test as CLI-specific"
    )
    config.addinivalue_line(
        "markers", "web: mark test as web API-specific"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to integration test files
        if "test_cli_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.cli)
        elif "test_web_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.web)
        elif "test_end_to_end" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)


# Custom pytest fixtures for mocking external dependencies
@pytest.fixture
def mock_llm_client(mocker):
    """Mock the LLM client for consistent testing."""
    mock_client = mocker.patch("src.document_to_anki.core.llm_client.LLMClient")
    mock_instance = mock_client.return_value
    
    # Default successful response
    mock_instance.generate_flashcards_from_text_sync.return_value = [
        {
            "question": "Test question",
            "answer": "Test answer",
            "card_type": "qa"
        }
    ]
    
    return mock_instance


@pytest.fixture
def mock_file_operations(mocker):
    """Mock file operations for testing without actual file I/O."""
    # Mock Path.exists to return True by default
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    # Mock Path.is_file to return True by default
    mocker.patch("pathlib.Path.is_file", return_value=True)
    
    # Mock Path.is_dir to return False by default
    mocker.patch("pathlib.Path.is_dir", return_value=False)
    
    # Mock file reading operations
    mocker.patch("pathlib.Path.read_text", return_value="Sample file content")
    
    return mocker


@pytest.fixture
def disable_logging():
    """Disable logging during tests to reduce noise."""
    import logging
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests."""
    import time
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    start_time = time.time()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    yield
    
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    execution_time = end_time - start_time
    memory_delta = end_memory - start_memory
    
    # Log performance metrics (could be extended to fail tests if thresholds exceeded)
    print(f"\nPerformance metrics:")
    print(f"  Execution time: {execution_time:.2f}s")
    print(f"  Memory delta: {memory_delta:.2f}MB")


# Error simulation fixtures
@pytest.fixture
def simulate_network_error(mocker):
    """Simulate network errors for testing error handling."""
    import requests
    mocker.patch("requests.post", side_effect=requests.ConnectionError("Network error"))
    mocker.patch("requests.get", side_effect=requests.ConnectionError("Network error"))


@pytest.fixture
def simulate_file_permission_error(mocker):
    """Simulate file permission errors."""
    mocker.patch("pathlib.Path.read_text", side_effect=PermissionError("Permission denied"))
    mocker.patch("pathlib.Path.write_text", side_effect=PermissionError("Permission denied"))


@pytest.fixture
def simulate_memory_error(mocker):
    """Simulate memory errors for testing resource handling."""
    def memory_error_side_effect(*args, **kwargs):
        raise MemoryError("Out of memory")
    
    return memory_error_side_effect