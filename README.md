# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Development

### Code Quality Tools

This project uses automated code quality tools to maintain consistent code style and catch common errors.

#### Available Commands

```bash
make help      # Display all available commands
make format    # Auto-format code with black and isort
make lint      # Run flake8 linter
make check     # Run all quality checks (without modifying code)
make test      # Run pytest tests
```

#### Before Committing Code

```bash
# 1. Format your code
make format

# 2. Verify all checks pass
make check

# 3. Commit your changes
git add .
git commit -m "Your commit message"
```

#### Tools Included

- **black**: Automatic code formatting (88 char line length)
- **isort**: Import organization and sorting
- **flake8**: PEP 8 compliance and linting
- **mypy**: Type checking (optional, run manually with `uv run mypy backend/ main.py`)

#### Using Shell Scripts

Alternative to make commands:
```bash
./scripts/format.sh    # Format code
./scripts/lint.sh      # Run linter
./scripts/check.sh     # Run all checks
```

For more details, see `frontend-changes.md`.

