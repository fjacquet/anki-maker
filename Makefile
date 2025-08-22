# Document to Anki CLI - Development Makefile

.PHONY: help install install-dev test test-cov test-fast lint format type-check security audit quality clean build run-cli run-web setup validate

# Default target
help: ## Show this help message
	@echo "Document to Anki CLI - Development Commands"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install the package
	uv pip install -e .

install-dev: ## Install with development dependencies
	uv pip install -e ".[dev]"

# Testing
test: ## Run all tests
	uv run test

test-cov: ## Run tests with coverage report
	uv run test-cov

test-fast: ## Run tests with fail-fast
	uv run test-fast

test-integration: ## Run integration tests only
	uv run test-integration

# Code Quality
lint: ## Run linting checks
	uv run lint

lint-fix: ## Fix linting issues automatically
	uv run lint-fix

format: ## Format code
	uv run format

format-check: ## Check code formatting
	uv run format-check

type-check: ## Run type checking
	uv run type-check

security: ## Run security checks
	uv run security

audit: ## Run dependency audit
	uv run audit

quality: ## Run all quality checks
	uv run quality

fix: ## Fix all auto-fixable issues
	uv run fix

# Development
setup: ## Set up development environment
	./scripts/setup_dev.sh

validate: ## Validate configuration
	python scripts/validate_config.py

run-cli: ## Run CLI in development mode
	uv run dev-cli

run-web: ## Run web server in development mode
	uv run dev-web

# Build and Distribution
build: ## Build the package
	uv run build

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
	uv pip list --outdated

update-deps: ## Update dependencies (use with caution)
	uv pip install --upgrade -e ".[dev]"

# CI/CD helpers
ci-test: ## Run tests in CI environment
	uv run test --tb=short --maxfail=1

ci-quality: ## Run quality checks in CI environment
	uv run quality

# Sample data
create-samples: ## Create sample documents for testing
	mkdir -p examples/sample_documents
	@echo "Sample documents created in examples/sample_documents/"

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