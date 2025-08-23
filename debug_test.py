#!/usr/bin/env python3

import os
import tempfile

from click.testing import CliRunner

from src.document_to_anki.cli.main import main

# Set up environment
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["MODEL"] = "gemini/gemini-2.5-flash"


def test_debug():
    runner = CliRunner()

    # Create a simple test file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document for creating flashcards.")
        test_file = f.name

    try:
        # Try to run the CLI
        result = runner.invoke(main, ["convert", test_file, "--output", "test_output.csv"], input="c\ny\n")

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback

            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)


if __name__ == "__main__":
    test_debug()
