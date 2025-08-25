#!/usr/bin/env python3
"""
Test script to validate CI-Makefile alignment.

This script tests that:
1. All Makefile targets used in CI work correctly
2. Exit codes are properly propagated
3. Error handling works as expected
4. Environment variables are handled correctly
5. Output formats are appropriate for CI

Usage:
    python test_makefile_ci_compatibility.py [--verbose] [--target TARGET]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class MakefileTestResult:
    """Result of a Makefile target test."""

    def __init__(
        self, target: str, success: bool, exit_code: int, stdout: str, stderr: str, duration: float, error_msg: str = ""
    ):
        self.target = target
        self.success = success
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.error_msg = error_msg


class CIMakefileValidator:
    """Validates CI-Makefile alignment."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: list[MakefileTestResult] = []
        self.project_root = Path.cwd()

    def log(self, message: str, color: str = ""):
        """Log a message with optional color."""
        if color:
            print(f"{color}{message}{Colors.END}")
        else:
            print(message)

    def log_verbose(self, message: str):
        """Log a verbose message."""
        if self.verbose:
            self.log(f"  {message}", Colors.BLUE)

    def run_make_target(self, target: str, env_vars: dict[str, str] = None) -> MakefileTestResult:
        """Run a Makefile target and capture results."""
        import time

        self.log_verbose(f"Running 'make {target}'...")

        # Set up environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Add mock environment for testing
        env.update(
            {
                "MOCK_LLM_RESPONSES": "true",
                # deepcode ignore HardcodedNonCryptoSecret/test: testing dummy secret
                "GEMINI_API_KEY": "mock-key-for-testing",
                "GITHUB_ACTIONS": "true",  # Simulate CI environment
            }
        )

        start_time = time.time()

        try:
            result = subprocess.run(
                ["make", target],
                capture_output=True,
                text=True,
                env=env,
                cwd=self.project_root,
                timeout=300,  # 5 minute timeout
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            return MakefileTestResult(
                target=target,
                success=success,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return MakefileTestResult(
                target=target,
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                error_msg="Timeout after 5 minutes",
            )
        except Exception as e:
            duration = time.time() - start_time
            return MakefileTestResult(
                target=target, success=False, exit_code=-1, stdout="", stderr="", duration=duration, error_msg=str(e)
            )

    def test_ci_targets(self) -> bool:
        """Test all CI-specific Makefile targets."""
        self.log(f"{Colors.BOLD}Testing CI-specific Makefile targets...{Colors.END}")

        # CI targets that should work in any environment
        ci_targets = ["check-uv", "check-env", "ci-setup", "ci-test", "ci-quality", "ci-validate", "ci-build"]

        all_passed = True

        for target in ci_targets:
            result = self.run_make_target(target)
            self.results.append(result)

            if result.success:
                self.log(f"  ✅ {target} - PASSED ({result.duration:.2f}s)", Colors.GREEN)
            else:
                self.log(f"  ❌ {target} - FAILED (exit code: {result.exit_code})", Colors.RED)
                if result.error_msg:
                    self.log(f"     Error: {result.error_msg}", Colors.RED)
                if self.verbose and result.stderr:
                    self.log(f"     stderr: {result.stderr[:200]}...", Colors.YELLOW)
                all_passed = False

        return all_passed

    def test_regular_targets_used_in_ci(self) -> bool:
        """Test regular Makefile targets that are used in CI."""
        self.log(f"{Colors.BOLD}Testing regular targets used in CI...{Colors.END}")

        # Regular targets used in CI workflow
        regular_targets = ["install-dev", "test-cov", "validate"]

        all_passed = True

        for target in regular_targets:
            result = self.run_make_target(target)
            self.results.append(result)

            if result.success:
                self.log(f"  ✅ {target} - PASSED ({result.duration:.2f}s)", Colors.GREEN)
            else:
                self.log(f"  ❌ {target} - FAILED (exit code: {result.exit_code})", Colors.RED)
                if result.error_msg:
                    self.log(f"     Error: {result.error_msg}", Colors.RED)
                if self.verbose and result.stderr:
                    self.log(f"     stderr: {result.stderr[:200]}...", Colors.YELLOW)
                all_passed = False

        return all_passed

    def test_error_propagation(self) -> bool:
        """Test that errors are properly propagated with correct exit codes."""
        self.log(f"{Colors.BOLD}Testing error propagation...{Colors.END}")

        # Test a target that should fail (non-existent target)
        result = self.run_make_target("non-existent-target")
        self.results.append(result)

        if not result.success and result.exit_code != 0:
            self.log(f"  ✅ Error propagation - PASSED (exit code: {result.exit_code})", Colors.GREEN)
            return True
        else:
            self.log("  ❌ Error propagation - FAILED (should have failed but didn't)", Colors.RED)
            return False

    def test_environment_handling(self) -> bool:
        """Test that environment variables are handled correctly."""
        self.log(f"{Colors.BOLD}Testing environment variable handling...{Colors.END}")

        # Test with different environment configurations
        test_cases = [
            {
                "name": "CI environment",
                "env": {"GITHUB_ACTIONS": "true", "MOCK_LLM_RESPONSES": "true"},
                "target": "check-env",
            },
            {
                "name": "Local environment",
                "env": {"GITHUB_ACTIONS": "", "GEMINI_API_KEY": "test-key"},
                "target": "check-env",
            },
        ]

        all_passed = True

        for test_case in test_cases:
            self.log_verbose(f"Testing {test_case['name']}...")
            result = self.run_make_target(test_case["target"], test_case["env"])

            if result.success:
                self.log(f"  ✅ {test_case['name']} - PASSED", Colors.GREEN)
            else:
                self.log(f"  ❌ {test_case['name']} - FAILED", Colors.RED)
                all_passed = False

        return all_passed

    def test_single_target(self, target: str) -> bool:
        """Test a single Makefile target."""
        self.log(f"{Colors.BOLD}Testing single target: {target}{Colors.END}")

        result = self.run_make_target(target)
        self.results.append(result)

        if result.success:
            self.log(f"  ✅ {target} - PASSED ({result.duration:.2f}s)", Colors.GREEN)
            if self.verbose and result.stdout:
                self.log(f"  stdout: {result.stdout[:500]}...", Colors.BLUE)
            return True
        else:
            self.log(f"  ❌ {target} - FAILED (exit code: {result.exit_code})", Colors.RED)
            if result.error_msg:
                self.log(f"     Error: {result.error_msg}", Colors.RED)
            if result.stderr:
                self.log(f"     stderr: {result.stderr}", Colors.YELLOW)
            if self.verbose and result.stdout:
                self.log(f"     stdout: {result.stdout}", Colors.BLUE)
            return False

    def generate_report(self) -> dict:
        """Generate a comprehensive test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            },
            "results": [],
        }

        for result in self.results:
            report["results"].append(
                {
                    "target": result.target,
                    "success": result.success,
                    "exit_code": result.exit_code,
                    "duration": result.duration,
                    "error_msg": result.error_msg,
                    "stdout_length": len(result.stdout),
                    "stderr_length": len(result.stderr),
                }
            )

        return report

    def print_summary(self):
        """Print a summary of test results."""
        report = self.generate_report()
        summary = report["summary"]

        self.log(f"\n{Colors.BOLD}=== TEST SUMMARY ==={Colors.END}")
        self.log(f"Total tests: {summary['total_tests']}")
        self.log(f"Passed: {summary['passed']}", Colors.GREEN)
        self.log(f"Failed: {summary['failed']}", Colors.RED if summary["failed"] > 0 else Colors.GREEN)
        self.log(f"Success rate: {summary['success_rate']:.1f}%")

        if summary["failed"] > 0:
            self.log(f"\n{Colors.BOLD}Failed targets:{Colors.END}")
            for result in self.results:
                if not result.success:
                    self.log(f"  - {result.target} (exit code: {result.exit_code})", Colors.RED)

    def run_full_validation(self) -> bool:
        """Run complete CI-Makefile validation."""
        self.log(f"{Colors.BOLD}🚀 Starting CI-Makefile Alignment Validation{Colors.END}")
        self.log(f"Project root: {self.project_root}")
        self.log("")

        # Check prerequisites
        if not (self.project_root / "Makefile").exists():
            self.log("❌ Makefile not found in project root", Colors.RED)
            return False

        if not (self.project_root / ".github" / "workflows" / "ci.yml").exists():
            self.log("❌ CI workflow file not found", Colors.RED)
            return False

        # Run all test suites
        all_passed = True

        all_passed &= self.test_ci_targets()
        all_passed &= self.test_regular_targets_used_in_ci()
        all_passed &= self.test_error_propagation()
        all_passed &= self.test_environment_handling()

        # Print summary
        self.print_summary()

        if all_passed:
            self.log(f"\n🎉 {Colors.GREEN}All CI-Makefile alignment tests PASSED!{Colors.END}")
        else:
            self.log(f"\n💥 {Colors.RED}Some CI-Makefile alignment tests FAILED!{Colors.END}")

        return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate CI-Makefile alignment")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--target", "-t", type=str, help="Test a single Makefile target")
    parser.add_argument("--report", "-r", type=str, help="Save detailed report to JSON file")

    args = parser.parse_args()

    validator = CIMakefileValidator(verbose=args.verbose)

    if args.target:
        # Test single target
        success = validator.test_single_target(args.target)
    else:
        # Run full validation
        success = validator.run_full_validation()

    # Save report if requested
    if args.report:
        report = validator.generate_report()
        with open(args.report, "w") as f:
            # deepcode ignore PT/test: test script
            json.dump(report, f, indent=2)
        print(f"Detailed report saved to {args.report}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
