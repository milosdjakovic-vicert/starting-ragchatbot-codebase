.PHONY: format lint check test install run help

help:
	@echo "Available commands:"
	@echo "  make install    - Install all dependencies"
	@echo "  make format     - Format code with black and isort"
	@echo "  make lint       - Run linters (flake8, mypy)"
	@echo "  make check      - Run all quality checks without modifying code"
	@echo "  make test       - Run tests"
	@echo "  make run        - Start the application"

install:
	@echo "Installing all dependencies..."
	uv sync
	@echo "Installing dev tools (black, isort, flake8, mypy, pytest)..."
	uv pip install black isort flake8 mypy
	uv pip install pytest pytest-asyncio pytest-mock pytest-cov httpx
	@echo "✓ Installation complete! You can now run 'make test' or 'make check'"

format:
	uv run isort backend/ main.py
	uv run black backend/ main.py

lint:
	uv run flake8 backend/ main.py
	@echo "Note: mypy type checking available but not enforced. Run 'uv run mypy backend/ main.py' to check types."

check:
	uv run isort --check-only backend/ main.py
	uv run black --check backend/ main.py
	uv run flake8 backend/ main.py
	@echo "✓ All quality checks passed!"
	@echo "Note: mypy type checking available but not enforced. Run 'uv run mypy backend/ main.py' to check types."

test:
	uv run pytest

run:
	./run.sh
