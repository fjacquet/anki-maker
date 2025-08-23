#!/usr/bin/env python3

import os
from unittest.mock import patch

from click.testing import CliRunner

from src.document_to_anki.cli.main import main


def test_invalid_model():
    """Test what happens with invalid model."""
    with patch.dict(os.environ, {"MODEL": "invalid/model"}, clear=True):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback

            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)


def test_missing_api_key():
    """Test what happens with missing API key."""
    with patch.dict(os.environ, {"MODEL": "gemini/gemini-2.5-flash"}, clear=True):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback

            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)


if __name__ == "__main__":
    print("=== Testing invalid model ===")
    test_invalid_model()
    print("\n=== Testing missing API key ===")
    test_missing_api_key()
