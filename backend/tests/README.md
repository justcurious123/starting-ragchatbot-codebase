# RAG System Testing Framework

This directory contains the comprehensive testing framework for the RAG (Retrieval-Augmented Generation) system.

## Overview

The testing framework provides:
- **API endpoint tests** - Comprehensive testing of FastAPI endpoints
- **Shared fixtures** - Reusable test components and mocks
- **Coverage reporting** - Code coverage analysis with HTML reports
- **Pytest configuration** - Optimized test execution settings

## Test Structure

```
backend/tests/
├── __init__.py              # Package marker
├── conftest.py              # Shared fixtures and test configuration
├── test_api_endpoints.py    # API endpoint tests
├── test_runner.py           # Test execution helper script
└── README.md               # This documentation
```

## Running Tests

### Quick Start
```bash
# Run all tests with coverage
uv run pytest backend/tests/ -v

# Run tests without coverage
uv run pytest backend/tests/ -v --no-cov

# Run only API tests
uv run pytest backend/tests/test_api_endpoints.py -v
```

### Using the Test Runner
```bash
# Run all tests with coverage (default)
python backend/tests/test_runner.py

# Run without coverage reporting
python backend/tests/test_runner.py --no-coverage

# Run only API endpoint tests
python backend/tests/test_runner.py --api-only

# Run tests matching a pattern
python backend/tests/test_runner.py -k "query"
```

## Test Coverage

The framework includes coverage reporting configured in `pyproject.toml`:
- **Terminal output**: Shows coverage summary with missing lines
- **HTML report**: Detailed coverage report in `htmlcov/` directory
- **XML report**: Machine-readable coverage data in `coverage.xml`

Current coverage focuses on API endpoints, with unit tests for individual components available for extension.

## Test Categories

### API Endpoint Tests (`test_api_endpoints.py`)

#### `/api/query` Endpoint Tests
- ✅ Successful query processing with various source formats
- ✅ Session management (with/without session_id)
- ✅ Error handling (invalid JSON, missing fields, system errors)
- ✅ Edge cases (empty queries, long text, special characters)

#### `/api/courses` Endpoint Tests  
- ✅ Course statistics retrieval
- ✅ Empty results handling
- ✅ Error scenarios
- ✅ Large dataset handling
- ✅ Method validation

#### Root Endpoint Tests
- ✅ Basic functionality
- ✅ Method validation

#### Middleware Tests
- ✅ CORS configuration
- ✅ Content-type handling

#### Response Model Tests
- ✅ QueryResponse validation
- ✅ CourseStats validation

#### Error Handling Tests
- ✅ 404 endpoints
- ✅ Malformed requests
- ✅ Missing headers

## Fixtures (`conftest.py`)

### Mock Components
- `mock_config`: Test configuration with temporary directories
- `mock_vector_store`: Mocked vector store operations
- `mock_ai_generator`: Mocked AI response generation
- `mock_session_manager`: Mocked session management
- `mock_rag_system`: Complete RAG system mock with all dependencies

### Test Data
- `sample_course`: Course model for testing
- `sample_course_chunks`: Course content chunks for testing
- `temp_docs_dir`: Temporary document directory with sample files

### Test App
- `test_app`: FastAPI test application without static file mounting issues
- `client`: TestClient for making HTTP requests

## Configuration

Pytest configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = [
    "-ra",                    # Show short test summary
    "--strict-markers",       # Strict marker validation
    "--strict-config",        # Strict configuration
    "--cov=backend",          # Coverage for backend module
    "--cov-report=term-missing:skip-covered",  # Terminal coverage
    "--cov-report=html:htmlcov",              # HTML coverage
    "--cov-report=xml",       # XML coverage for CI
]
testpaths = ["backend/tests"]  # Test discovery path
asyncio_mode = "auto"         # Automatic async test handling
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]
```

## Dependencies

Test-specific dependencies added to `pyproject.toml`:
- `pytest>=8.0.0` - Test framework
- `pytest-asyncio>=0.23.0` - Async test support
- `pytest-cov>=4.0.0` - Coverage reporting
- `httpx>=0.25.0` - HTTP client for FastAPI testing

## Architecture Decisions

### Static File Mounting Solution
The original FastAPI app mounts static files that don't exist in the test environment. The testing framework solves this by:
1. Creating a separate test app in `conftest.py` 
2. Defining API endpoints inline without static file mounting
3. Using comprehensive mocking to isolate API logic from file system dependencies

### Mock Strategy
- **Complete isolation**: All external dependencies (vector store, AI, sessions) are mocked
- **Realistic responses**: Mocks return data structures matching production code
- **Error simulation**: Tests include error scenarios for robust error handling validation
- **Async support**: AsyncMock used for async operations like RAG queries

### Test Organization
- **Class-based grouping**: Tests organized by endpoint/functionality
- **Descriptive naming**: Test names clearly indicate what is being tested
- **Edge case coverage**: Tests include boundary conditions and error scenarios

## Extending Tests

To add new tests:

1. **New endpoint tests**: Add to `test_api_endpoints.py` following the existing class structure
2. **Unit tests**: Create new files like `test_vector_store.py` for component testing  
3. **Integration tests**: Add tests that exercise multiple components together
4. **New fixtures**: Add reusable components to `conftest.py`

Example new test class:
```python
class TestNewEndpoint:
    """Test cases for the /api/new endpoint"""
    
    def test_new_endpoint_success(self, client, mock_rag_system):
        """Test successful operation"""
        # Test implementation
        pass
```

## Continuous Integration

The framework is ready for CI/CD integration:
- XML coverage reports for pipeline integration
- Configurable verbosity and output formats
- Clear exit codes for build status
- No external dependencies in test execution