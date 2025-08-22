#!/bin/bash

# Quality check script for document-to-anki-cli
set -e

echo "🔍 Running code quality and security checks..."
echo

echo "📝 Running ruff linting..."
ruff check src/ --fix
echo "✅ Ruff linting passed"
echo

echo "🎨 Running ruff formatting..."
ruff format src/
echo "✅ Ruff formatting completed"
echo

echo "🔍 Running mypy type checking..."
mypy src/document_to_anki
echo "✅ MyPy type checking passed"
echo

echo "🔒 Running bandit security scanning..."
bandit -r src/document_to_anki
echo "✅ Bandit security scanning passed"
echo

echo "🛡️ Running pip-audit dependency vulnerability checking..."
pip-audit
echo "✅ Pip-audit dependency checking passed"
echo

echo "🧪 Running tests with coverage..."
pytest
echo "✅ All tests passed with required coverage"
echo

echo "🎉 All quality checks passed successfully!"