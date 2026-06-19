# Document to Anki CLI — Development Makefile
#
# Canonical interface aligned to the fjacquet/ci standard (do not rename the
# standard targets: install, tools, lint, format, test, build, vuln, sbom,
# security, docs, coverage-upload, release, ci, clean).
# Repo-specific helpers (run-cli, run-web, validate, docker-*) are preserved below.

.DEFAULT_GOAL := all
DIST ?= dist

.PHONY: all clean install tools lint format test build vuln sbom security docs coverage-upload release ci \
	help run-cli run-web validate setup type-check docs-serve \
	docker-dev docker-prod docker-down

help: ## Show this help message
	@echo "Document to Anki CLI — Development Commands"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── fjacquet/ci canonical targets ──────────────────────────────────────────

all: clean lint test build  ## Full local validation (clean + lint + test + build)

clean:  ## Remove build/test artifacts
	rm -rf $(DIST) site .coverage coverage.xml *.sarif htmlcov build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete

install:  ## Install all dependencies (runtime + dev + docs)
	uv sync --all-extras --all-groups

tools: install  ## Alias for install (fjacquet/ci contract)

lint:  ## Lint + format check (read-only)
	uv run ruff check .
	uv run ruff format --check .

format:  ## Auto-format the codebase
	uv run ruff format .

test:  ## Run tests with coverage (xml + term-missing)
	uv run pytest --cov --cov-report=xml --cov-report=term-missing

build:  ## Build the wheel/sdist
	uv build

vuln:  ## OSV vulnerability scan against uv.lock
	uvx osv-scanner scan --lockfile=uv.lock || true

sbom:  ## Generate a CycloneDX SBOM to dist/sbom.cdx.json
	mkdir -p $(DIST)
	uv run cyclonedx-py environment --output-format JSON --output-file $(DIST)/sbom.cdx.json

security:  ## Semgrep SAST scan (advisory; non-blocking — CodeQL/osv are the blocking gates)
	uvx semgrep scan --config auto --skip-unknown-extensions || true

docs:  ## Build the MkDocs site (strict) into ./site
	uv run mkdocs build --strict --site-dir site

coverage-upload:  ## Upload coverage.xml to Codecov
	uvx --from codecov-cli codecov upload-process --file coverage.xml || true

release:  ## Build distributables (no PyPI publish target configured for this repo)
	uv build

ci: lint test build  ## Canonical CI target (lint test build)

# ── Repo-specific helpers (not part of the fjacquet/ci contract) ────────────

type-check:  ## Run mypy type checks
	uv run mypy src/document_to_anki

setup: install  ## Set up local development environment

validate:  ## Validate runtime configuration
	uv run python scripts/validate_config.py

run-cli:  ## Run the CLI in development mode
	uv run document-to-anki

run-web:  ## Run the web server in development mode
	uv run document-to-anki-web

docs-serve:  ## Serve the docs locally with live reload (http://127.0.0.1:8000)
	uv run mkdocs serve

docker-dev:  ## Run development environment with external config
	docker-compose -f docker-compose.yml -f configs/docker/development.yml up --build

docker-prod:  ## Run production environment with external config
	docker-compose -f docker-compose.yml -f configs/docker/production.yml up -d --build

docker-down:  ## Stop all docker services
	docker-compose down
