"""
Test data loader utility for end-to-end tests.

This module provides utilities to load external test data files,
making tests cleaner and more maintainable.
"""

from pathlib import Path
from typing import Any

import yaml


class TestDataLoader:
    """Load external test data and configurations."""

    def __init__(self, fixtures_dir: Path = None):
        """
        Initialize the test data loader.

        Args:
            fixtures_dir: Directory containing test fixtures
        """
        if fixtures_dir is None:
            fixtures_dir = Path(__file__).parent

        self.fixtures_dir = Path(fixtures_dir)
        self.documents_dir = self.fixtures_dir / "sample_documents"
        self._cache: dict[str, Any] = {}

    def load_yaml_config(self, config_name: str) -> dict[str, Any]:
        """
        Load a YAML configuration file.

        Args:
            config_name: Name of the config file (without .yml extension)

        Returns:
            Dictionary containing the configuration data
        """
        if config_name in self._cache:
            return self._cache[config_name]

        config_path = self.fixtures_dir / f"{config_name}.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Test config file not found: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        self._cache[config_name] = config_data
        return config_data

    def load_document_content(self, document_name: str) -> str:
        """
        Load content from a test document file.

        Args:
            document_name: Name of the document file (with extension)

        Returns:
            Content of the document as string
        """
        document_path = self.documents_dir / document_name

        if not document_path.exists():
            raise FileNotFoundError(f"Test document not found: {document_path}")

        return document_path.read_text(encoding="utf-8").strip()

    def get_document_path(self, document_name: str) -> Path:
        """
        Get the path to a test document file.

        Args:
            document_name: Name of the document file (with extension)

        Returns:
            Path to the document file
        """
        return self.documents_dir / document_name

    def create_temp_document(
        self, temp_dir: Path, document_name: str, content: str = None, repeat_count: int = 1
    ) -> Path:
        """
        Create a temporary document file for testing.

        Args:
            temp_dir: Temporary directory to create the file in
            document_name: Name for the temporary file
            content: Content to write (if None, loads from existing document)
            repeat_count: Number of times to repeat the content

        Returns:
            Path to the created temporary file
        """
        if content is None:
            content = self.load_document_content(document_name)

        # Repeat content if requested
        if repeat_count > 1:
            content = (content + "\n\n") * repeat_count

        temp_file = temp_dir / document_name
        temp_file.write_text(content, encoding="utf-8")
        return temp_file

    def get_mock_llm_responses(self) -> dict[str, Any]:
        """Get mock LLM responses configuration."""
        return self.load_yaml_config("mock_llm_responses")

    def get_test_config(self) -> dict[str, Any]:
        """Get test configuration settings."""
        return self.load_yaml_config("test_config")

    def get_mock_response_for_content(self, text_content: str) -> list[dict[str, str]]:
        """
        Get appropriate mock response based on text content.

        Args:
            text_content: The text content to analyze

        Returns:
            List of mock flashcard dictionaries
        """
        responses_config = self.get_mock_llm_responses()
        responses = responses_config.get("responses", {})
        config = responses_config.get("config", {})

        case_sensitive = config.get("case_sensitive", False)
        if not case_sensitive:
            text_content = text_content.lower()

        # Check each response type for keyword matches
        for _response_type, response_data in responses.items():
            trigger_keywords = response_data.get("trigger_keywords", [])

            if not case_sensitive:
                trigger_keywords = [kw.lower() for kw in trigger_keywords]

            # Check if any trigger keywords are in the content
            if any(keyword in text_content for keyword in trigger_keywords):
                return response_data.get("flashcards", [])

        # Return generic response if no matches found
        generic_response = responses.get("generic", {})
        return generic_response.get("flashcards", [])

    def create_mock_llm_function(self):
        """
        Create a mock function for LLM responses.

        Returns:
            Function that can be used to mock LLM calls
        """

        def mock_generate_flashcards(text):
            return self.get_mock_response_for_content(text)

        return mock_generate_flashcards

    def get_timeout_for_test(self, test_name: str) -> int:
        """
        Get timeout setting for a specific test.

        Args:
            test_name: Name of the test method

        Returns:
            Timeout in seconds
        """
        test_config = self.get_test_config()
        timeouts = test_config.get("timeouts", {})
        return timeouts.get(test_name, 60)  # Default 60 seconds

    def get_performance_expectations(self, operation: str) -> dict[str, Any]:
        """
        Get performance expectations for an operation.

        Args:
            operation: Name of the operation (e.g., 'document_processing')

        Returns:
            Dictionary with performance expectations
        """
        test_config = self.get_test_config()
        performance = test_config.get("performance", {})
        return performance.get(operation, {})

    def get_document_size_config(self, size_category: str) -> dict[str, Any]:
        """
        Get document size configuration.

        Args:
            size_category: Size category ('small', 'medium', 'large')

        Returns:
            Dictionary with size configuration
        """
        test_config = self.get_test_config()
        sizes = test_config.get("document_sizes", {})
        return sizes.get(size_category, {})

    def clear_cache(self):
        """Clear the configuration cache."""
        self._cache.clear()


# Global instance for easy access
test_data_loader = TestDataLoader()


def load_test_document(document_name: str) -> str:
    """
    Convenience function to load a test document.

    Args:
        document_name: Name of the document file

    Returns:
        Content of the document
    """
    return test_data_loader.load_document_content(document_name)


def get_test_document_path(document_name: str) -> Path:
    """
    Convenience function to get a test document path.

    Args:
        document_name: Name of the document file

    Returns:
        Path to the document
    """
    return test_data_loader.get_document_path(document_name)


def create_mock_llm_responses():
    """
    Convenience function to create mock LLM response function.

    Returns:
        Mock function for LLM responses
    """
    return test_data_loader.create_mock_llm_function()


if __name__ == "__main__":
    # Example usage
    loader = TestDataLoader()

    print("Available test documents:")
    for doc_file in loader.documents_dir.glob("*.txt"):
        print(f"  - {doc_file.name}")
    for doc_file in loader.documents_dir.glob("*.md"):
        print(f"  - {doc_file.name}")

    print("\nTest configuration:")
    config = loader.get_test_config()
    print(f"  - Timeouts: {list(config.get('timeouts', {}).keys())}")
    print(f"  - Performance settings: {list(config.get('performance', {}).keys())}")

    print("\nMock LLM responses:")
    responses = loader.get_mock_llm_responses()
    for response_type in responses.get("responses", {}):
        print(f"  - {response_type}")

    # Test mock response generation
    python_content = loader.load_document_content("python_basics.txt")
    mock_responses = loader.get_mock_response_for_content(python_content)
    print(f"\nMock responses for Python content: {len(mock_responses)} flashcards")
