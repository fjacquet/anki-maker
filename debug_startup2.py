#!/usr/bin/env python3

import os
from unittest.mock import patch

from click.testing import CliRunner

from src.document_to_anki.cli.main import main


def test_invalid_model_with_command():
    """Test what happens with invalid model when running a command."""
    with patch.dict(os.environ, {"MODEL": "invalid/model"}, clear=True):
        runner = CliRunner()
        # Try to run convert command instead of --help
        result = runner.invoke(main, ["convert", "--help"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback

            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)


if __name__ == "__main__":
    print("=== Testing invalid model with convert command ===")
    test_invalid_model_with_command()
