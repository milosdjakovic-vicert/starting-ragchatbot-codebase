#!/bin/bash
# Run all quality checks

set -e

echo "=== Code Quality Checks ==="
echo ""

echo "1. Checking import sorting..."
uv run isort --check-only backend/ main.py

echo ""
echo "2. Checking code formatting..."
uv run black --check backend/ main.py

echo ""
echo "3. Running flake8 linter..."
uv run flake8 backend/ main.py

echo ""
echo "=== All checks passed! ==="
echo ""
echo "Note: mypy type checking available but not enforced. Run 'uv run mypy backend/ main.py' to check types."
