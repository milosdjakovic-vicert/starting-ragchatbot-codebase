# Quick Testing Guide

## Running Tests

### Basic Commands
```bash
# Run all tests (recommended)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with quiet output
uv run pytest -q

# Run specific test file
uv run pytest tests/test_session_manager.py

# Run specific test
uv run pytest tests/test_session_manager.py::TestSessionManager::test_create_session

# Run tests matching pattern
uv run pytest -k "test_query"
```

### Coverage Commands (Optional)
Coverage is optional - only run when you need coverage reports:

```bash
# Run with coverage
uv run pytest --cov=backend

# Coverage with missing lines (most useful)
uv run pytest --cov=backend --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=backend --cov-report=html
open htmlcov/index.html

# Clean coverage between runs if needed
rm -rf .coverage* htmlcov/
```

### Useful Options
```bash
# Stop on first failure
uv run pytest -x

# Show local variables on failure
uv run pytest -l

# Run last failed tests
uv run pytest --lf

# Run failed tests first, then all
uv run pytest --ff

# Quiet mode (less output)
uv run pytest -q

# Very verbose (show all)
uv run pytest -vv
```

## Test Organization

```
tests/
├── test_session_manager.py    # Conversation sessions
├── test_document_processor.py # Document parsing
├── test_vector_store.py       # Vector database
├── test_search_tools.py       # Search functionality
├── test_ai_generator.py       # AI interactions
├── test_rag_system.py         # Main orchestrator
└── test_app.py                # API models
```

## Writing New Tests

### Basic Test Template
```python
import pytest

class TestMyComponent:
    """Tests for MyComponent"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        component = MyComponent()

        # Act
        result = component.do_something()

        # Assert
        assert result == expected_value
```

### Using Fixtures
```python
@pytest.fixture
def sample_data():
    """Create sample data for testing"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture"""
    assert sample_data["key"] == "value"
```

### Mocking
```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test using mocks"""
    mock_obj = Mock()
    mock_obj.method.return_value = "mocked"

    result = mock_obj.method()
    assert result == "mocked"
    mock_obj.method.assert_called_once()
```

## Coverage Goals

- **Critical modules**: 95%+ coverage
- **Business logic**: 90%+ coverage
- **Overall**: 80%+ coverage
- **Configuration**: Coverage not required

## Best Practices

1. **Test Names**: Use descriptive names
   - ✅ `test_query_returns_answer_with_sources`
   - ❌ `test_query`

2. **One Assertion Per Test**: Focus tests
   - Test one thing at a time
   - Makes failures easier to debug

3. **Arrange-Act-Assert**: Structure tests clearly
   ```python
   # Arrange: Set up test data
   # Act: Execute the code being tested
   # Assert: Verify the results
   ```

4. **Use Fixtures**: Share setup code
   - Reduces duplication
   - Improves maintainability

5. **Mock External Dependencies**
   - Don't call real APIs in tests
   - Use temporary files/databases
   - Fast, reliable tests

## Common Patterns

### Testing Exceptions
```python
def test_raises_error():
    with pytest.raises(ValueError, match="Invalid input"):
        function_that_raises()
```

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

### Testing Async Code
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

## Troubleshooting

### Tests Won't Run
```bash
# Check pytest installation
uv run pytest --version

# Verify Python path
uv run python -c "import sys; print(sys.path)"

# Clear cache
uv run pytest --cache-clear
```

### Import Errors
```bash
# Check backend path is correct
ls backend/

# Verify conftest.py exists
ls tests/conftest.py
```

### Coverage Issues
```bash
# Clean coverage data
rm -rf .coverage htmlcov/

# Re-run with coverage
uv run pytest --cov=backend
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install uv
      - run: uv sync
      - run: uv run pytest --cov=backend
      - run: uv run pytest --cov=backend --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Guide](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
