#!/bin/bash
# Clean Python cache and generated files

set -euo pipefail

echo "Cleaning Python cache and generated files..."

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true

# Clean testing and linting caches
rm -rf .ruff_cache .mypy_cache .pytest_cache
rm -rf htmlcov/ .coverage

echo "Cache cleaned successfully"