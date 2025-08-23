#!/usr/bin/env python3
"""
Compare local Makefile execution results with CI environment simulation.

This script runs Makefile targets in both local and simulated CI environments
to ensure they produce consistent results and handle errors the same way.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


class LocalCIComparator:
    """Compares local and CI execution of Makefile targets."""

    def __init__(self):
        self.project_root = Path.cwd()

    def run_in_local_env(self, target: str) -> tuple[int, str, str]:
        """Run Makefile target in local environment."""
        env = os.environ.copy()
        env.update({"MOCK_LLM_RESPONSES": "true", "GEMINI_API_KEY": "mock-key-for-testing"})

        result = subprocess.run(["make", target], capture_output=True, text=True, env=env, cwd=self.project_root)

        return result.returncode, result.stdout, result.stderr

    def run_in_ci_env(self, target: str) -> tuple[int, str, str]:
        """Run Makefile target in simulated CI environment."""
        env = os.environ.copy()
        env.update(
            {
                "GITHUB_ACTIONS": "true",
                "MOCK_LLM_RESPONSES": "true",
                "GEMINI_API_KEY": "mock-key-for-testing",
                "CI": "true",
            }
        )

        result = subprocess.run(["make", target], capture_output=True, text=True, env=env, cwd=self.project_root)

        return result.returncode, result.stdout, result.stderr

    def compare_target_execution(self, target: str) -> dict:
        """Compare execution of a target in local vs CI environment."""
        print(f"🔄 Comparing '{target}' execution...")

        # Run in local environment
        local_exit, local_stdout, local_stderr = self.run_in_local_env(target)

        # Run in CI environment
        ci_exit, ci_stdout, ci_stderr = self.run_in_ci_env(target)

        # Compare results
        exit_code_match = local_exit == ci_exit

        # For output comparison, we focus on key indicators rather than exact match
        # since CI might have different formatting
        output_consistent = True
        if local_exit == 0 and ci_exit != 0:
            output_consistent = False
        elif local_exit != 0 and ci_exit == 0:
            output_consistent = False

        return {
            "target": target,
            "local": {
                "exit_code": local_exit,
                "stdout_length": len(local_stdout),
                "stderr_length": len(local_stderr),
                "success": local_exit == 0,
            },
            "ci": {
                "exit_code": ci_exit,
                "stdout_length": len(ci_stdout),
                "stderr_length": len(ci_stderr),
                "success": ci_exit == 0,
            },
            "comparison": {
                "exit_code_match": exit_code_match,
                "output_consistent": output_consistent,
                "overall_match": exit_code_match and output_consistent,
            },
        }

    def run_comparison_suite(self) -> dict:
        """Run comparison for all important CI targets."""
        targets_to_test = ["check-uv", "check-env", "ci-setup", "ci-quality", "ci-validate", "ci-build"]

        results = []
        overall_success = True

        print("🚀 Starting Local vs CI Environment Comparison")
        print("=" * 50)

        for target in targets_to_test:
            try:
                result = self.compare_target_execution(target)
                results.append(result)

                if result["comparison"]["overall_match"]:
                    print(f"  ✅ {target} - CONSISTENT")
                else:
                    print(f"  ❌ {target} - INCONSISTENT")
                    print(f"     Local exit: {result['local']['exit_code']}, CI exit: {result['ci']['exit_code']}")
                    overall_success = False

            except Exception as e:
                print(f"  💥 {target} - ERROR: {e}")
                overall_success = False
                results.append({"target": target, "error": str(e), "comparison": {"overall_match": False}})

        # Summary
        consistent_count = sum(1 for r in results if r.get("comparison", {}).get("overall_match", False))
        total_count = len(results)

        print("\n📊 Comparison Summary:")
        print(f"   Consistent: {consistent_count}/{total_count}")
        print(f"   Success Rate: {consistent_count / total_count * 100:.1f}%")

        if overall_success:
            print("🎉 All targets show consistent behavior between local and CI!")
        else:
            print("⚠️  Some targets show inconsistent behavior - needs investigation")

        return {
            "results": results,
            "summary": {
                "total": total_count,
                "consistent": consistent_count,
                "success_rate": consistent_count / total_count * 100,
                "overall_success": overall_success,
            },
        }


def main():
    """Main entry point."""
    comparator = LocalCIComparator()

    # Run the comparison
    comparison_results = comparator.run_comparison_suite()

    # Save detailed results
    with open("ci_comparison_results.json", "w") as f:
        json.dump(comparison_results, f, indent=2)

    print("\n📄 Detailed results saved to ci_comparison_results.json")

    # Exit with appropriate code
    sys.exit(0 if comparison_results["summary"]["overall_success"] else 1)


if __name__ == "__main__":
    main()
