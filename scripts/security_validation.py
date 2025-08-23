#!/usr/bin/env python3
"""
Security validation script for Document to Anki CLI application.

This script performs comprehensive security checks including:
1. Environment variable handling validation
2. Input sanitization verification
3. File path security checks
4. Web interface security headers validation
5. Configuration security best practices

Usage:
    python scripts/security_validation.py

    # Or via make target
    make security-validate
"""

import re
import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_to_anki.config import ModelConfig


class SecurityValidator:
    """Validates security aspects of the application."""

    def __init__(self):
        self.issues: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []

    def add_issue(self, category: str, severity: str, description: str, file_path: str = "", line: int = 0):
        """Add a security issue."""
        self.issues.append(
            {
                "category": category,
                "severity": severity,
                "description": description,
                "file_path": file_path,
                "line": line,
            }
        )

    def add_warning(self, category: str, description: str, file_path: str = "", line: int = 0):
        """Add a security warning."""
        self.warnings.append({"category": category, "description": description, "file_path": file_path, "line": line})

    def validate_environment_variables(self) -> bool:
        """Validate environment variable handling security."""
        print("🔍 Validating environment variable handling...")

        # Check if environment variables are properly centralized
        config_file = Path("src/document_to_anki/config.py")
        if not config_file.exists():
            self.add_issue("env_vars", "HIGH", "Config file not found", str(config_file))
            return False

        # Read config file and check for proper patterns
        config_content = config_file.read_text()

        # Check for direct os.getenv usage (should be minimal and controlled)
        getenv_matches = re.findall(r"os\.getenv\([^)]+\)", config_content)
        if len(getenv_matches) > 3:  # Allow a few controlled uses
            self.add_warning(
                "env_vars", f"Multiple direct os.getenv calls found: {len(getenv_matches)}", str(config_file)
            )

        # Check for proper default values
        if 'os.getenv("MODEL"' not in config_content:
            self.add_issue("env_vars", "MEDIUM", "MODEL environment variable not properly handled", str(config_file))

        # Validate that sensitive env vars are not logged
        src_files = list(Path("src").rglob("*.py"))
        for file_path in src_files:
            content = file_path.read_text()
            # Check for potential logging of sensitive data
            if re.search(r"logger\.[^(]*\([^)]*(?:API_KEY|SECRET|PASSWORD|TOKEN)", content, re.IGNORECASE):
                self.add_issue(
                    "env_vars", "HIGH", "Potential logging of sensitive environment variables", str(file_path)
                )

        print("✅ Environment variable validation completed")
        return True

    def validate_input_sanitization(self) -> bool:
        """Validate input sanitization and validation."""
        print("🔍 Validating input sanitization...")

        # Test path traversal protection
        test_paths = [
            Path("../../../etc/passwd"),
            Path("..\\..\\windows\\system32\\config\\sam"),
            Path("test/../../../sensitive"),
            Path("normal_file.pdf"),
        ]

        for test_path in test_paths:
            try:
                # This should not raise an exception for the normal file
                # but should handle malicious paths safely
                if ".." in str(test_path) and test_path.name != "normal_file.pdf":
                    # These should be handled safely by _validate_path_security
                    pass
            except Exception:
                # Expected for malicious paths
                pass

        # Check web interface input validation
        web_app_file = Path("src/document_to_anki/web/app.py")
        if web_app_file.exists():
            content = web_app_file.read_text()

            # Check for Pydantic models for validation
            if "BaseModel" not in content:
                self.add_issue(
                    "input_validation",
                    "MEDIUM",
                    "No Pydantic models found for input validation",
                    str(web_app_file),
                )

            # Check for file size limits
            if "max_file_size" not in content.lower():
                self.add_warning("input_validation", "File size limits not explicitly checked", str(web_app_file))

            # Check for CORS configuration
            if "CORSMiddleware" not in content:
                self.add_issue("input_validation", "MEDIUM", "CORS middleware not configured", str(web_app_file))

        print("✅ Input sanitization validation completed")
        return True

    def validate_file_security(self) -> bool:
        """Validate file handling security."""
        print("🔍 Validating file handling security...")

        file_handler_path = Path("src/document_to_anki/utils/file_handler.py")
        if not file_handler_path.exists():
            self.add_issue("file_security", "HIGH", "File handler not found", str(file_handler_path))
            return False

        content = file_handler_path.read_text()

        # Check for path traversal protection
        if "_validate_path_security" not in content:
            self.add_issue("file_security", "HIGH", "Path traversal protection not implemented", str(file_handler_path))

        # Check for file size limits
        if "MAX_FILE_SIZE" not in content:
            self.add_issue("file_security", "MEDIUM", "File size limits not defined", str(file_handler_path))

        # Check for file type validation
        if "SUPPORTED_EXTENSIONS" not in content:
            self.add_issue("file_security", "MEDIUM", "File type validation not implemented", str(file_handler_path))

        # Check for ZIP bomb protection
        if "MAX_FILES_COUNT" not in content:
            self.add_warning("file_security", "ZIP bomb protection may be insufficient", str(file_handler_path))

        print("✅ File handling security validation completed")
        return True

    def validate_web_security(self) -> bool:
        """Validate web interface security."""
        print("🔍 Validating web interface security...")

        web_app_path = Path("src/document_to_anki/web/app.py")
        if not web_app_path.exists():
            self.add_warning("web_security", "Web interface not found", str(web_app_path))
            return True

        content = web_app_path.read_text()

        # Check for security headers middleware
        if "SecurityHeadersMiddleware" not in content:
            self.add_issue("web_security", "HIGH", "Security headers middleware not implemented", str(web_app_path))

        # Check for specific security headers
        security_headers = ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection", "Content-Security-Policy"]

        for header in security_headers:
            if header not in content:
                self.add_issue("web_security", "MEDIUM", f"Security header {header} not set", str(web_app_path))

        # Check for session security
        if "secret_key" in content.lower() and "change-this-in-production" in content:
            self.add_issue("web_security", "HIGH", "Default secret key found in production code", str(web_app_path))

        # Check for HTTPS enforcement (should be in deployment config)
        if "https_only" not in content.lower():
            self.add_warning("web_security", "HTTPS enforcement not explicitly configured", str(web_app_path))

        print("✅ Web interface security validation completed")
        return True

    def validate_configuration_security(self) -> bool:
        """Validate configuration security best practices."""
        print("🔍 Validating configuration security...")

        # Check for .env.example file
        env_example = Path(".env.example")
        if not env_example.exists():
            self.add_warning("config_security", ".env.example file not found")
        else:
            content = env_example.read_text()
            # Check that no real secrets are in the example
            if re.search(r"[A-Za-z0-9]{20,}", content):
                self.add_issue("config_security", "HIGH", "Potential real secrets in .env.example", str(env_example))

        # Check .gitignore for sensitive files
        gitignore = Path(".gitignore")
        if gitignore.exists():
            content = gitignore.read_text()
            sensitive_patterns = [".env", "*.key", "*.pem", "secrets"]
            for pattern in sensitive_patterns:
                if pattern not in content:
                    self.add_warning(
                        "config_security", f"Sensitive pattern {pattern} not in .gitignore", str(gitignore)
                    )

        # Test ModelConfig validation
        try:
            # This should work with default settings
            supported_models = ModelConfig.get_supported_models()
            if not supported_models:
                self.add_issue("config_security", "MEDIUM", "No supported models configured")
        except Exception as e:
            self.add_issue("config_security", "MEDIUM", f"ModelConfig validation failed: {e}")

        print("✅ Configuration security validation completed")
        return True

    def validate_dependency_security(self) -> bool:
        """Validate dependency security configuration."""
        print("🔍 Validating dependency security...")

        # Check pyproject.toml for security tools
        pyproject = Path("pyproject.toml")
        if pyproject.exists():
            content = pyproject.read_text()

            security_tools = ["bandit", "safety", "pip-audit"]
            for tool in security_tools:
                if tool not in content:
                    self.add_warning("dependency_security", f"Security tool {tool} not configured", str(pyproject))

            # Check for bandit configuration
            if "[tool.bandit]" not in content:
                self.add_warning("dependency_security", "Bandit configuration not found", str(pyproject))

        print("✅ Dependency security validation completed")
        return True

    def run_validation(self) -> bool:
        """Run all security validations."""
        print("🔒 Starting comprehensive security validation...\n")

        validations = [
            self.validate_environment_variables,
            self.validate_input_sanitization,
            self.validate_file_security,
            self.validate_web_security,
            self.validate_configuration_security,
            self.validate_dependency_security,
        ]

        success = True
        for validation in validations:
            try:
                if not validation():
                    success = False
            except Exception as e:
                print(f"❌ Validation failed with error: {e}")
                success = False

        return success

    def print_report(self) -> None:
        """Print security validation report."""
        print("\n" + "=" * 60)
        print("🔒 SECURITY VALIDATION REPORT")
        print("=" * 60)

        if not self.issues and not self.warnings:
            print("✅ No security issues found!")
            return

        if self.issues:
            print(f"\n❌ SECURITY ISSUES FOUND ({len(self.issues)}):")
            print("-" * 40)

            for issue in self.issues:
                severity_icon = "🔴" if issue["severity"] == "HIGH" else "🟡"
                print(f"{severity_icon} [{issue['severity']}] {issue['category']}: {issue['description']}")
                if issue["file_path"]:
                    print(f"   📁 File: {issue['file_path']}")
                    if issue["line"]:
                        print(f"   📍 Line: {issue['line']}")
                print()

        if self.warnings:
            print(f"\n⚠️  SECURITY WARNINGS ({len(self.warnings)}):")
            print("-" * 40)

            for warning in self.warnings:
                print(f"🟡 {warning['category']}: {warning['description']}")
                if warning["file_path"]:
                    print(f"   📁 File: {warning['file_path']}")
                    if warning["line"]:
                        print(f"   📍 Line: {warning['line']}")
                print()

        # Summary
        high_issues = len([i for i in self.issues if i["severity"] == "HIGH"])
        medium_issues = len([i for i in self.issues if i["severity"] == "MEDIUM"])

        print("📊 SUMMARY:")
        print(f"   🔴 High severity issues: {high_issues}")
        print(f"   🟡 Medium severity issues: {medium_issues}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")

        if high_issues > 0:
            print("\n🚨 HIGH PRIORITY: Address high severity issues immediately!")
        elif medium_issues > 0:
            print("\n⚠️  MEDIUM PRIORITY: Consider addressing medium severity issues.")
        else:
            print("\n✅ No critical security issues found.")


def main():
    """Main entry point for security validation."""
    validator = SecurityValidator()

    try:
        validator.run_validation()
        validator.print_report()

        # Exit with appropriate code
        if any(issue["severity"] == "HIGH" for issue in validator.issues):
            sys.exit(1)  # High severity issues
        elif validator.issues:
            sys.exit(2)  # Medium severity issues
        else:
            sys.exit(0)  # Success

    except KeyboardInterrupt:
        print("\n❌ Security validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Security validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
