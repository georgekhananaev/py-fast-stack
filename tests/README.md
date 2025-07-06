# PyFastStack Tests

Tests for PyFastStack API endpoints. These tests require the server to be running.

**Created by [George Khananaev](https://george.khananaev.com/)**

## Prerequisites

1. **Start the server** in one terminal:
   ```bash
   uv run python run.py
   ```
   
2. **Note the root credentials** displayed when the server starts

3. **Update test configuration** if needed:
   - The tests expect the server to run on `http://localhost:8000`
   - The superuser tests use the root user credentials

## Running Tests

In a separate terminal, while the server is running:

```bash
# Install test dependencies
uv sync --extra test

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_auth.py -v

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run performance tests only
uv run pytest tests/test_performance.py -v -s
```

## Test Structure

- `test_auth.py` - Authentication endpoints (register, login, token validation)
- `test_users.py` - User CRUD operations and profile management
- `test_performance.py` - Load testing and performance benchmarks

## Important Notes

1. **Server must be running** - Tests connect to the actual running server
2. **Database state** - Tests create and use test users. Some tests may fail if users already exist
3. **Root user** - Superuser tests require the root user to exist with known credentials
4. **Cleanup** - Tests try to clean up after themselves, but some test data may persist

## Troubleshooting

If tests fail:

1. Make sure the server is running on `http://localhost:8000`
2. Check that the database is initialized (root user exists)
3. Some tests may fail on repeated runs if test users already exist
4. For a clean test run, delete the database and restart the server

## Performance Testing

The performance tests (`test_performance.py`) will output detailed metrics:

```bash
uv run pytest tests/test_performance.py -v -s
```

This will show:
- Response times (average, min, max)
- Requests per second
- Concurrent user handling
- Load test results