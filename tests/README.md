# Test Suite

This directory contains comprehensive pytest tests for the RAG chatbot application.

## Test Coverage

**Overall Coverage: 81%**

### Module Coverage:
- `ai_generator.py`: 100% ✅
- `session_manager.py`: 100% ✅
- `models.py`: 100% ✅
- `rag_system.py`: 100% ✅
- `search_tools.py`: 96% ✅
- `document_processor.py`: 96% ✅
- `vector_store.py`: 83% ⚠️
- `app.py`: 0% (FastAPI endpoints tested via integration)
- `config.py`: 0% (Configuration module)

## Running Tests

### Run all tests:
```bash
uv run pytest
```

### Run tests with coverage (optional):
Coverage is optional - only use when you need coverage reports:

```bash
# With coverage summary
uv run pytest --cov=backend --cov-report=term-missing

# With HTML coverage report
uv run pytest --cov=backend --cov-report=html
# Then open htmlcov/index.html in browser
```

### Run specific test file:
```bash
uv run pytest tests/test_session_manager.py
```

### Run tests matching a pattern:
```bash
uv run pytest -k "test_query"
```

## Test Structure

### test_session_manager.py (17 tests)
- Tests for conversation session management
- Message history tracking
- Session creation and cleanup

### test_document_processor.py (17 tests)
- Document parsing and processing
- Text chunking with overlap
- Course metadata extraction
- Multi-lesson document handling

### test_vector_store.py (29 tests)
- ChromaDB integration
- Vector search functionality
- Course metadata storage
- Semantic search with filters

### test_search_tools.py (26 tests)
- CourseSearchTool functionality
- CourseOutlineTool functionality
- ToolManager registration and execution
- Source tracking

### test_ai_generator.py (12 tests)
- Claude API integration
- Tool-calling workflow
- Conversation history handling
- Response generation

### test_rag_system.py (14 tests)
- Main RAG system orchestration
- Course folder processing
- Query handling with sessions
- Analytics

### test_app.py (5 tests)
- Pydantic model validation
- API model structures

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `setup_test_environment`: Creates temporary frontend directory

Individual test files include specialized fixtures:
- `mock_vector_store`: Mock ChromaDB storage
- `mock_rag_system`: Mock RAG system
- `sample_course`: Sample course data
- `temp_chroma_path`: Temporary ChromaDB path

## Test Markers

Available markers (defined in pytest.ini):
- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow running tests

Use markers:
```bash
pytest -m unit  # Run only unit tests
pytest -m "not slow"  # Skip slow tests
```

## Dependencies

Testing dependencies (installed automatically with `uv sync`):
- pytest>=8.0.0
- pytest-cov>=4.1.0
- pytest-asyncio>=0.21.0
- httpx>=0.25.0
- pytest-mock>=3.12.0

## Notes

- FastAPI endpoint tests are intentionally simplified to avoid static file mounting complications in test environment
- Core business logic is thoroughly tested with 96-100% coverage
- Vector store tests use temporary ChromaDB instances
- AI generator tests use mocks to avoid actual API calls
