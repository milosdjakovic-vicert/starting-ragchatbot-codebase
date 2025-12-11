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

## Testing

The application includes a comprehensive test suite with 120 tests covering all core functionality.

### Running Tests

**Quick test run:**
```bash
uv run pytest
```

**With verbose output:**
```bash
uv run pytest -v
```

**With coverage report:**
```bash
uv run pytest --cov=backend --cov-report=term-missing
```

### Test Structure

The test suite covers:
- **Session Management** (17 tests) - Conversation history and session handling
- **Document Processing** (17 tests) - Text chunking and metadata extraction
- **Vector Store** (29 tests) - ChromaDB integration and semantic search
- **Search Tools** (26 tests) - Course search and outline retrieval
- **AI Generator** (12 tests) - Claude API integration and tool calling
- **RAG System** (14 tests) - Main orchestrator and query processing
- **API Models** (5 tests) - Pydantic model validation

**Coverage:** 81% overall with core modules at 96-100%

### Test Documentation

For detailed testing information, see:
- `tests/README.md` - Comprehensive test documentation
- `TESTING_GUIDE.md` - Quick reference guide
- `TEST_SUMMARY.md` - Implementation details

