#!/bin/bash
# Run linting checks

set -e

echo "Running flake8..."
uv run flake8 backend/ main.py

echo ""
echo "Linting complete!"
echo "Note: mypy type checking available but not enforced. Run 'uv run mypy backend/ main.py' to check types."
