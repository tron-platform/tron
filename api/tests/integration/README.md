# Integration Tests

Integration tests for the Tron API that test the full HTTP request/response cycle including authentication, database operations, and endpoint handlers.

## Overview

These tests use FastAPI's `TestClient` to make real HTTP requests to the API endpoints, with a real in-memory SQLite database. This ensures that:

- HTTP request/response serialization works correctly
- Authentication and authorization are properly enforced
- Database operations (CRUD) function as expected
- Error handling returns appropriate HTTP status codes
- Dependencies between services, repositories, and handlers work together

## Running Integration Tests

### Run all integration tests:
```bash
pytest tests/integration/ -v
```

### Run specific test file:
```bash
pytest tests/integration/test_auth_api.py -v
```

### Run with coverage:
```bash
pytest tests/integration/ --cov=app --cov-report=term-missing
```

### Run only integration tests (exclude unit tests):
```bash
pytest tests/integration/ -m integration -v
```

## Test Structure

### Fixtures (in `conftest.py`)

- `test_db`: Creates a fresh in-memory SQLite database for each test
- `client`: FastAPI TestClient with database override
- `admin_user`: Creates an admin user in the test database
- `regular_user`: Creates a regular user in the test database
- `admin_token`: Gets authentication token for admin user
- `user_token`: Gets authentication token for regular user

### Test Files

- `test_auth_api.py`: Authentication endpoints (login, register, refresh, profile)
- `test_clusters_api.py`: Cluster management endpoints
- `test_applications_api.py`: Application management endpoints

## Writing New Integration Tests

1. Import necessary fixtures from `conftest.py`
2. Use the `client` fixture to make HTTP requests
3. Use `admin_token` or `user_token` for authenticated requests
4. Create test data using fixtures or directly in the test
5. Assert on HTTP status codes and response JSON

Example:
```python
def test_create_resource_success(client, admin_token):
    """Test successful resource creation."""
    response = client.post(
        "/resources/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "test-resource"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test-resource"
```

## Differences from Unit Tests

| Aspect | Unit Tests | Integration Tests |
|--------|-----------|------------------|
| **Scope** | Single service/function | Full HTTP endpoint |
| **Database** | Mocked | Real in-memory DB |
| **Dependencies** | Mocked | Real dependencies |
| **Speed** | Fast | Slower |
| **Coverage** | Business logic | End-to-end flow |

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: The `test_db` fixture automatically cleans up after each test
3. **Authentication**: Always test both authenticated and unauthenticated scenarios
4. **Authorization**: Test role-based access control (admin vs regular user)
5. **Error Cases**: Test both success and error scenarios (404, 400, 401, 403)

## Notes

- Tests use SQLite in-memory database for speed
- Each test gets a fresh database (no data leakage between tests)
- Authentication tokens are generated using real JWT logic
- All database operations are committed and can be queried
