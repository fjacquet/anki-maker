#!/usr/bin/env python3
"""
Validate that the CI workflow uses the correct Makefile targets.

This script analyzes the CI workflow file to ensure it uses Makefile targets
instead of direct commands, providing consistency between local and CI environments.
"""

import sys
from pathlib import Path
from typing import Any

import yaml


class CIWorkflowValidator:
    """Validates CI workflow alignment with Makefile."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.ci_file = self.project_root / ".github" / "workflows" / "ci.yml"
        self.makefile = self.project_root / "Makefile"

    def load_ci_workflow(self) -> dict[str, Any]:
        """Load and parse the CI workflow file."""
        if not self.ci_file.exists():
            raise FileNotFoundError(f"CI workflow file not found: {self.ci_file}")

        with open(self.ci_file) as f:
            return yaml.safe_load(f)

    def get_makefile_targets(self) -> list[str]:
        """Extract all targets from the Makefile."""
        if not self.makefile.exists():
            raise FileNotFoundError(f"Makefile not found: {self.makefile}")

        targets = []
        with open(self.makefile) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and ":" in line:
                    target = line.split(":")[0].strip()
                    if target and not target.startswith(".") and not target.startswith("$"):
                        targets.append(target)

        return sorted(set(targets))

    def extract_ci_commands(self, workflow: dict[str, Any]) -> list[str]:
        """Extract all run commands from the CI workflow."""
        commands = []

        jobs = workflow.get("jobs", {})
        for job_config in jobs.values():
            steps = job_config.get("steps", [])
            for step in steps:
                if "run" in step:
                    run_command = step["run"]
                    if isinstance(run_command, str):
                        commands.append(run_command.strip())

        return commands

    def validate_makefile_usage(self) -> dict[str, Any]:
        """Validate that CI uses Makefile targets appropriately."""
        workflow = self.load_ci_workflow()
        makefile_targets = self.get_makefile_targets()
        ci_commands = self.extract_ci_commands(workflow)

        # Expected Makefile targets that should be used in CI
        expected_make_commands = [
            "make install-dev",
            "make test-cov",
            "make ci-quality",
            "make ci-test-integration",
            "make validate",
            "make ci-build",
        ]

        # Check which expected commands are present
        found_make_commands = []
        missing_make_commands = []

        for expected in expected_make_commands:
            found = False
            for command in ci_commands:
                if expected in command:
                    found_make_commands.append(expected)
                    found = True
                    break
            if not found:
                missing_make_commands.append(expected)

        # Check for direct commands that should use Makefile instead
        problematic_commands = []
        for command in ci_commands:
            # Check for direct uv/python commands that should go through Makefile
            if (
                any(
                    pattern in command.lower()
                    for pattern in [
                        "uv pip install",
                        "python -m pip",
                        "pip install",
                        "pytest ",
                        "ruff ",
                        "mypy ",
                        "bandit ",
                        "pip-audit",
                    ]
                )
                and "make " not in command
            ):
                problematic_commands.append(command)

        return {
            "makefile_targets": makefile_targets,
            "ci_commands": ci_commands,
            "found_make_commands": found_make_commands,
            "missing_make_commands": missing_make_commands,
            "problematic_commands": problematic_commands,
            "alignment_score": len(found_make_commands) / len(expected_make_commands) * 100,
        }

    def print_validation_report(self):
        """Print a detailed validation report."""
        try:
            results = self.validate_makefile_usage()

            print("🔍 CI-Makefile Alignment Validation Report")
            print("=" * 50)

            print(f"\n✅ Found Makefile commands in CI ({len(results['found_make_commands'])}):")
            for cmd in results["found_make_commands"]:
                print(f"  - {cmd}")

            if results["missing_make_commands"]:
                print(f"\n⚠️  Missing expected Makefile commands ({len(results['missing_make_commands'])}):")
                for cmd in results["missing_make_commands"]:
                    print(f"  - {cmd}")

            if results["problematic_commands"]:
                print(f"\n❌ Direct commands that should use Makefile ({len(results['problematic_commands'])}):")
                for cmd in results["problematic_commands"]:
                    print(f"  - {cmd}")

            print(f"\n📊 Alignment Score: {results['alignment_score']:.1f}%")

            if results["alignment_score"] >= 90:
                print("🎉 Excellent CI-Makefile alignment!")
                return True
            elif results["alignment_score"] >= 70:
                print("👍 Good CI-Makefile alignment with room for improvement")
                return True
            else:
                print("⚠️  Poor CI-Makefile alignment - needs improvement")
                return False

        except Exception as e:
            print(f"❌ Error validating CI workflow: {e}")
            return False


def main():
    """Main entry point."""
    validator = CIWorkflowValidator()
    success = validator.print_validation_report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
