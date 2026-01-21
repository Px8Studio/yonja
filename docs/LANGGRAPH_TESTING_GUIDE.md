# LangGraph Integration Testing Guide

## Overview

This guide covers testing strategies for the LangGraph Dev Server integration, including unit tests, integration tests, and end-to-end testing scenarios.

## Test Structure

```
tests/
├── unit/
│   └── test_langgraph_client.py      # Client HTTP logic
├── integration/
│   └── test_graph_api.py             # FastAPI routes
└── conftest.py                        # Shared fixtures
```

## Running Tests

### All Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/yonca --cov-report=html

# Specific test file
pytest tests/integration/test_graph_api.py -v

# Specific test
pytest tests/integration/test_graph_api.py::test_graph_invoke_success -v
```

### Unit Tests Only

```bash
pytest tests/unit/ -v
```

### Integration Tests Only

```bash
pytest tests/integration/ -v
```

## Unit Tests

### LangGraph Client (`test_langgraph_client.py`)

**Coverage**: HTTP client logic, request formatting, error handling

#### Test Categories

1. **Initialization Tests**
   - Default configuration
   - Custom configuration
   - URL normalization

2. **Invoke Tests**
   - Successful invocation
   - With all parameters
   - HTTP errors
   - Connection errors
   - Empty responses

3. **Stream Tests**
   - Successful streaming
   - Empty responses
   - Parsing SSE events

4. **Thread Management Tests**
   - Thread creation
   - Minimal parameters

5. **Health Check Tests**
   - Healthy server
   - Unhealthy server
   - Connection errors

6. **Payload Construction Tests**
   - Request structure validation
   - Parameter mapping

#### Example: Testing Invoke

```python
@pytest.mark.asyncio
async def test_invoke_success(client, mock_httpx_client):
    """Test successful graph invocation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "messages": [
            {"role": "assistant", "content": "Response text"}
        ]
    }
    mock_httpx_client.post.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await client.invoke(
            message="Test message",
            thread_id="test-thread",
            user_id="test-user",
        )

    assert result == "Response text"
```

#### Running Unit Tests

```bash
# All unit tests
pytest tests/unit/test_langgraph_client.py -v

# Specific test
pytest tests/unit/test_langgraph_client.py::test_invoke_success -v

# With coverage
pytest tests/unit/test_langgraph_client.py --cov=src/yonca/langgraph/client
```

## Integration Tests

### Graph API Routes (`test_graph_api.py`)

**Coverage**: FastAPI endpoints, request validation, response formatting

#### Test Categories

1. **Graph Invoke Tests**
   - Successful invocation
   - With system prompt
   - With scenario context
   - Missing fields
   - Empty messages

2. **Graph Stream Tests**
   - Successful streaming
   - Missing fields

3. **Thread Management Tests**
   - Create thread
   - Get thread history
   - Delete thread
   - Not found scenarios

4. **Health Check Tests**
   - Service health

5. **Error Handling Tests**
   - Invalid JSON
   - Invalid parameters

6. **Workflow Tests**
   - Full workflow (create → invoke → history → delete)
   - Multiple invocations

#### Example: Testing Full Workflow

```python
@pytest.mark.asyncio
async def test_full_workflow(client: AsyncClient):
    """Test complete workflow."""
    # 1. Create thread
    create_response = await client.post(
        "/api/v1/graph/threads",
        json={"user_id": "test-user", "farm_id": "test-farm"},
    )
    thread_id = create_response.json()["thread_id"]

    # 2. Invoke graph
    invoke_response = await client.post(
        "/api/v1/graph/invoke",
        json={
            "message": "Kartof haqqında məlumat ver",
            "thread_id": thread_id,
            "user_id": "test-user",
            "language": "az",
        },
    )
    assert "response" in invoke_response.json()

    # 3. Get history
    history_response = await client.get(f"/api/v1/graph/threads/{thread_id}")
    assert history_response.status_code == 200

    # 4. Delete thread
    delete_response = await client.delete(f"/api/v1/graph/threads/{thread_id}")
    assert delete_response.status_code == 200
```

#### Running Integration Tests

```bash
# All integration tests
pytest tests/integration/test_graph_api.py -v

# Specific test
pytest tests/integration/test_graph_api.py::test_full_workflow -v

# Skip slow tests
pytest tests/integration/test_graph_api.py -v -m "not slow"
```

## Test Fixtures

### Shared Fixtures (`conftest.py`)

```python
import pytest
from httpx import AsyncClient
from yonca.api.main import app

@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_message():
    """Sample message payload."""
    return {
        "message": "Test message",
        "thread_id": "test-thread",
        "user_id": "test-user",
        "language": "az",
    }
```

## Mocking Strategies

### Mock HTTP Client

```python
from unittest.mock import AsyncMock, MagicMock
import httpx

@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    mock = AsyncMock(spec=httpx.AsyncClient)
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock()
    return mock
```

### Mock LangGraph Response

```python
mock_response = MagicMock()
mock_response.status_code = 200
mock_response.json.return_value = {
    "messages": [
        {"role": "assistant", "content": "Response"}
    ]
}
mock_httpx_client.post.return_value = mock_response
```

### Mock Streaming Response

```python
async def mock_stream_iter():
    yield b'data: {"messages": [{"content": "Chunk 1"}]}\n\n'
    yield b'data: {"messages": [{"content": "Chunk 2"}]}\n\n'

mock_response = MagicMock()
mock_response.__aenter__ = AsyncMock(return_value=mock_response)
mock_response.__aexit__ = AsyncMock()
mock_response.aiter_bytes = mock_stream_iter

mock_httpx_client.stream.return_value = mock_response
```

## Test Markers

### Custom Markers

```python
# pytest.ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Usage

```python
@pytest.mark.slow
@pytest.mark.integration
async def test_full_workflow(client):
    """Test complete workflow (slow)."""
    pass
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: yonca_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/yonca_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/ -v --cov=src/yonca --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Manual Testing

### Test LangGraph Client

```bash
# Start LangGraph Dev Server
$env:PYTHONPATH = ".\src"
.\.venv\Scripts\langgraph.exe dev

# Run Python script
python -c "
import asyncio
from yonca.langgraph.client import LangGraphClient

async def test():
    client = LangGraphClient()

    # Test health
    healthy = await client.health()
    print(f'Health: {healthy}')

    # Test invoke
    response = await client.invoke(
        message='Kartof haqqında məlumat ver',
        thread_id='test-123',
        user_id='test-user',
        language='az'
    )
    print(f'Response: {response}')

asyncio.run(test())
"
```

### Test FastAPI Routes

```bash
# Start FastAPI
python -m uvicorn yonca.api.main:app --reload

# Test with curl
curl -X POST http://localhost:8000/api/v1/graph/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Kartof haqqında məlumat ver",
    "thread_id": "test-123",
    "user_id": "test-user",
    "language": "az"
  }'

# Test health
curl http://localhost:8000/api/v1/graph/health
```

### Test Chainlit API Mode

```bash
# Terminal 1: Start FastAPI
python -m uvicorn yonca.api.main:app --reload

# Terminal 2: Start Chainlit in API mode
$env:INTEGRATION_MODE = "api"
chainlit run demo-ui/app.py -w --port 8501

# Open http://localhost:8501 and test
```

## Performance Testing

### Load Testing with Locust

```python
from locust import HttpUser, task, between

class GraphAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def invoke_graph(self):
        self.client.post("/api/v1/graph/invoke", json={
            "message": "Test message",
            "thread_id": f"test-{self.user_id}",
            "user_id": f"user-{self.user_id}",
            "language": "az",
        })

    @task(2)
    def health_check(self):
        self.client.get("/api/v1/graph/health")
```

Run load test:

```bash
locust -f tests/performance/test_load.py --host=http://localhost:8000
```

## Test Coverage

### Generate Coverage Report

```bash
# HTML report
pytest tests/ --cov=src/yonca --cov-report=html

# Terminal report
pytest tests/ --cov=src/yonca --cov-report=term

# XML report (for CI)
pytest tests/ --cov=src/yonca --cov-report=xml
```

### Coverage Goals

- **Unit Tests**: > 80% coverage
- **Integration Tests**: > 70% coverage
- **Critical Paths**: 100% coverage

## Troubleshooting

### Tests Fail with ModuleNotFoundError

```bash
# Set PYTHONPATH
$env:PYTHONPATH = ".\src"

# Or install package in development mode
pip install -e .
```

### Tests Timeout

```bash
# Increase timeout
pytest tests/ -v --timeout=300

# Skip slow tests
pytest tests/ -v -m "not slow"
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Run migrations
alembic upgrade head
```

### Redis Connection Issues

```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli ping
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Fixtures**: Use fixtures for common setup
3. **Mocking**: Mock external dependencies
4. **Assertions**: Use clear, specific assertions
5. **Documentation**: Document test purpose and expectations
6. **Coverage**: Aim for high but meaningful coverage
7. **Performance**: Keep tests fast, mark slow tests
8. **CI/CD**: Run tests on every commit

## Summary

✅ **Unit tests** for LangGraph client (23 tests)
✅ **Integration tests** for Graph API routes (25+ tests)
✅ **Fixtures** for common test setup
✅ **Mocking** strategies documented
✅ **CI/CD** workflow template
✅ **Manual testing** procedures
✅ **Performance testing** setup

## Next Steps

1. ✅ Tests created
2. ⏳ Run test suite
3. ⏳ Fix any failing tests
4. ⏳ Set up CI/CD pipeline
5. ⏳ Add performance benchmarks

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [httpx Testing](https://www.python-httpx.org/advanced/#mocking)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
