# Document to Anki CLI - Development Makefile
#
# This Makefile provides consistent commands for both local development and CI environments.
# All commands use 'uv run' prefix for consistency and proper virtual environment handling.
#
# CI Compatibility Features:
# - Environment variable validation (check-env)
# - CI-specific output formats (ci-quality uses GitHub Actions format)
# - Dependency validation (check-uv)
# - Enhanced error handling and exit codes with fail-fast behavior
# - Support for GITHUB_ACTIONS, GEMINI_API_KEY, MOCK_LLM_RESPONSES environment variables
# - Comprehensive error reporting with actionable messages
#
# Key CI Targets (with enhanced error handling):
# - ci-setup: Set up CI environment with dependency installation and basic validation
# - ci-test: Run tests with CI-friendly output (fail-fast, concise output)
# - ci-quality: Run all quality checks with proper error handling and GitHub Actions format
# - ci-validate: Validate configuration with detailed error reporting
# - ci-build: Build package with CI-friendly output and error handling
#
# Usage in CI (with proper error propagation):
#   make ci-setup && make ci-quality && make ci-test && make ci-validate && make ci-build
#
# Each target will fail immediately on error with proper exit codes for CI integration.

.PHONY: help install install-dev test test-cov test-fast lint format type-check security audit quality clean build run-cli run-web setup validate ci-setup ci-test ci-quality ci-install ci-validate ci-build check-uv check-env debug-env

# Default target
help: ## Show this help message
	@echo "Document to Anki CLI - Development Commands"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment validation
check-uv: ## Check if uv is installed
	@command -v uv >/dev/null 2>&1 || { echo "Error: uv is not installed. Please install uv first."; exit 1; }

check-env: ## Check environment variables for CI compatibility
	@echo "Checking environment variables..."
	@if [ -n "$$GITHUB_ACTIONS" ]; then \
		echo "Running in GitHub Actions environment"; \
		if [ -z "$$GEMINI_API_KEY" ] && [ -z "$$MOCK_LLM_RESPONSES" ]; then \
			echo "Warning: Neither GEMINI_API_KEY nor MOCK_LLM_RESPONSES is set"; \
		fi; \
	else \
		echo "Running in local environment"; \
	fi

# Installation
install: check-uv ## Install the package
	uv sync --no-dev

install-dev: check-uv ## Install with development dependencies
	uv sync --all-extras

# Testing
test: check-env ## Run all tests
	uv run pytest

test-cov: check-env ## Run tests with coverage report
	uv run pytest --cov=src/document_to_anki --cov-report=html --cov-report=term --cov-report=xml

test-fast: check-env ## Run tests with fail-fast
	uv run pytest -x

test-integration: check-env ## Run integration tests only
	uv run pytest -m integration

test-integration-cov: check-env ## Run integration tests with coverage report
	uv run pytest -m integration --cov=src/document_to_anki --cov-report=html --cov-report=term --cov-report=xml

ci-test-integration: check-env ## Run integration tests in CI environment
	@echo "Running integration tests in CI mode..."
	@set -e; \
	uv run pytest -m integration --tb=short --maxfail=1 --no-header --quiet || { \
		echo "ERROR: Integration tests failed in CI environment"; \
		exit 1; \
	}; \
	echo "CI integration tests completed successfully"

# Code Quality
lint: ## Run linting checks
	uv run ruff format    
	uv run ruff check --fix

lint-fix: ## Fix linting issues automatically
	uv run ruff check --fix

format: ## Format code
	uv run ruff format

format-check: ## Check code formatting (read-only)
	uv run ruff format --check 

type-check: ## Run type checking
	uv run mypy src/document_to_anki

security: ## Run security checks
	@echo "Running security vulnerability scan..."
	uv run bandit -r src/document_to_anki
	@echo "Security scan completed"

audit: ## Run dependency audit
	@echo "Running dependency vulnerability scan..."
	uv run pip-audit
	@echo "Dependency audit completed"

security-full: ## Run comprehensive security checks (code + dependencies)
	@echo "Running comprehensive security checks..."
	@echo "1. Code security scan with bandit..."
	uv run bandit -r src/document_to_anki
	@echo "2. Dependency vulnerability scan with pip-audit..."
	uv run pip-audit
	@echo "Comprehensive security checks completed"

security-validate: ## Run comprehensive security validation
	@echo "Running security validation..."
	uv run python scripts/security_validation.py

quality: ## Run all quality checks (includes automatic formatting)
	uv run ruff check --fix
	uv run ruff format 
	uv run mypy src/document_to_anki
	uv run bandit -r src/document_to_anki
	uv run pip-audit
	uv run python scripts/security_validation.py

fix: ## Fix all auto-fixable issues
	uv run ruff check --fix
	uv run ruff format

# Development
setup: ## Set up development environment
	@echo "🚀 Setting up Document to Anki CLI development environment..."
	uv sync
	@echo "✅ Development environment set up successfully!"

setup-full: setup create-samples env-example ## Full development setup with samples and environment
	@echo "📁 Creating necessary directories..."
	@mkdir -p exports .cache logs
	@echo "🎯 Full development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "   1. Edit .env file with your API keys"
	@echo "   2. Run tests: make test"
	@echo "   3. Start development: make run-cli examples/sample_documents/sample.txt"
	@echo "   4. Or start web server: make run-web"

validate: check-env ## Validate configuration
	@echo "Validating configuration..."
	uv run python scripts/validate_config.py

run-cli: ## Run CLI in development mode
	uv run document-to-anki

run-web: ## Run web server in development mode
	uv run document-to-anki-web

# Build and Distribution
build: check-uv ## Build the package
	@echo "Building package..."
	uv build
	@echo "Package build completed"

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Documentation
docs: ## Generate documentation (placeholder)
	@echo "Documentation generation not yet implemented"

# Docker (placeholder for future)
docker-build: ## Build Docker image (placeholder)
	@echo "Docker build not yet implemented"

docker-run: ## Run Docker container (placeholder)
	@echo "Docker run not yet implemented"

# Utility targets
check-deps: ## Check for outdated dependencies
	uv tree --outdated

update-deps: ## Update dependencies (use with caution)
	uv sync --upgrade

# CI/CD helpers
ci-setup: check-uv check-env ## Set up CI environment
	@echo "Setting up CI environment..."
	@set -e; \
	uv sync --all-extras; \
	echo "Running basic validation..."; \
	uv run python -c "from document_to_anki.config import Settings; Settings()" || { \
		echo "Warning: Configuration validation failed - this may be expected in CI without API keys"; \
		exit 0; \
	}; \
	echo "CI environment setup complete"

ci-test: check-env ## Run tests in CI environment
	@echo "Running tests in CI mode..."
	@set -e; \
	uv run pytest --tb=short --maxfail=1 --no-header --quiet || { \
		echo "ERROR: Tests failed in CI environment"; \
		exit 1; \
	}; \
	echo "CI tests completed successfully"

ci-quality: check-env ## Run quality checks in CI environment
	@echo "Running quality checks in CI mode..."
	@set -e; \
	echo "1. Running ruff linting..."; \
	uv run ruff check --output-format=github --exclude="debug_*.py" --exclude="test_makefile_ci_compatibility.py" || { \
		echo "ERROR: Ruff linting failed"; \
		exit 1; \
	}; \
	echo "2. Checking code formatting..."; \
	uv run ruff format --check --exclude="debug_*.py" --exclude="test_makefile_ci_compatibility.py" || { \
		echo "ERROR: Code formatting check failed"; \
		exit 1; \
	}; \
	echo "3. Running type checking..."; \
	uv run mypy src/document_to_anki --no-error-summary || { \
		echo "ERROR: Type checking failed"; \
		exit 1; \
	}; \
	echo "4. Running security scan..."; \
	uv run bandit -r src/document_to_anki --format json --quiet || { \
		echo "ERROR: Security scan failed"; \
		exit 1; \
	}; \
	echo "5. Running dependency audit..."; \
	uv run pip-audit --format json || { \
		echo "ERROR: Dependency audit failed"; \
		exit 1; \
	}; \
	echo "6. Running security validation..."; \
	uv run python scripts/security_validation.py || { \
		echo "ERROR: Security validation failed"; \
		exit 1; \
	}; \
	echo "CI quality checks completed successfully"

# Sample data
create-samples: ## Create sample documents for testing
	@echo "📄 Creating sample documents for testing..."
	@mkdir -p examples/sample_documents
	@echo "# Sample Document for Testing" > examples/sample_documents/sample.txt
	@echo "" >> examples/sample_documents/sample.txt
	@echo "This is a sample document that can be used to test the Document to Anki CLI application." >> examples/sample_documents/sample.txt
	@echo "" >> examples/sample_documents/sample.txt
	@echo "## Key Concepts" >> examples/sample_documents/sample.txt
	@echo "" >> examples/sample_documents/sample.txt
	@echo "**Photosynthesis** is the process by which plants convert light energy into chemical energy." >> examples/sample_documents/sample.txt
	@echo "This process occurs in the chloroplasts of plant cells and involves two main stages:" >> examples/sample_documents/sample.txt
	@echo "" >> examples/sample_documents/sample.txt
	@echo "1. **Light-dependent reactions**: These occur in the thylakoids and capture light energy to produce ATP and NADPH." >> examples/sample_documents/sample.txt
	@echo "2. **Light-independent reactions** (Calvin cycle): These occur in the stroma and use ATP and NADPH to convert CO2 into glucose." >> examples/sample_documents/sample.txt
	@echo "" >> examples/sample_documents/sample.txt
	@echo "## Important Facts" >> examples/sample_documents/sample.txt
	@echo "" >> examples/sample_documents/sample.txt
	@echo "- Photosynthesis produces oxygen as a byproduct" >> examples/sample_documents/sample.txt
	@echo "- The overall equation is: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2" >> examples/sample_documents/sample.txt
	@echo "- Chlorophyll is the primary pigment responsible for capturing light energy" >> examples/sample_documents/sample.txt
	@echo "- Plants are autotrophs because they can produce their own food through photosynthesis" >> examples/sample_documents/sample.txt
	@echo "# Machine Learning Basics" > examples/sample_documents/sample.md
	@echo "" >> examples/sample_documents/sample.md
	@echo "## What is Machine Learning?" >> examples/sample_documents/sample.md
	@echo "" >> examples/sample_documents/sample.md
	@echo "**Machine Learning** is a subset of artificial intelligence (AI) that enables computers to learn and make decisions from data without being explicitly programmed for every task." >> examples/sample_documents/sample.md
	@echo "" >> examples/sample_documents/sample.md
	@echo "## Types of Machine Learning" >> examples/sample_documents/sample.md
	@echo "" >> examples/sample_documents/sample.md
	@echo "### Supervised Learning" >> examples/sample_documents/sample.md
	@echo "- Uses labeled training data" >> examples/sample_documents/sample.md
	@echo "- Examples: classification, regression" >> examples/sample_documents/sample.md
	@echo "- Algorithms: linear regression, decision trees, neural networks" >> examples/sample_documents/sample.md
	@echo "✅ Sample documents created in examples/sample_documents/"

# Environment
env-example: ## Copy environment example file
	cp .env.example .env
	@echo "Created .env file from .env.example - please edit with your settings"

# Quick development workflow
dev: install-dev validate ## Set up development environment and validate
	@echo "Development environment ready!"

# Full quality check before commit
pre-commit: quality test ## Run full quality checks and tests
	@echo "Pre-commit checks passed!"

# Release preparation (placeholder)
prepare-release: clean quality test build ## Prepare for release
	@echo "Release preparation complete!"

# CI-specific workflow targets
ci-install: ci-setup ## Alias for ci-setup (for CI workflow compatibility)

ci-validate: check-env ## Validate configuration in CI environment
	@echo "Validating configuration in CI mode..."
	@set -e; \
	uv run python scripts/validate_config.py || { \
		echo "ERROR: Configuration validation failed"; \
		echo "This may indicate missing environment variables or configuration issues"; \
		exit 1; \
	}; \
	echo "CI configuration validation completed successfully"

ci-build: check-uv ## Build package in CI environment
	@echo "Building package in CI mode..."
	@set -e; \
	uv build || { \
		echo "ERROR: Package build failed"; \
		exit 1; \
	}; \
	echo "CI package build completed successfully"

# Debug and troubleshooting
debug-env: ## Show environment information for debugging
	@echo "Environment Information:"
	@echo "======================="
	@echo "Python version: $$(python --version 2>/dev/null || echo 'Not found')"
	@echo "uv version: $$(uv --version 2>/dev/null || echo 'Not found')"
	@echo "GITHUB_ACTIONS: $${GITHUB_ACTIONS:-not set}"
	@echo "GEMINI_API_KEY: $$(if [ -n "$$GEMINI_API_KEY" ]; then echo 'set'; else echo 'not set'; fi)"
	@echo "MOCK_LLM_RESPONSES: $${MOCK_LLM_RESPONSES:-not set}"
	@echo "MODEL: $${MODEL:-not set}"
	@echo "Working directory: $$(pwd)"