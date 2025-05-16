# uninest Tests

This directory contains test files for the uninest application backend using pytest.

## Tests Structure

The tests are organized by feature:

- `conftest.py` - Contains pytest fixtures shared across test files
- `test_auth.py` - Tests for authentication endpoints (register, login)
- `test_users.py` - Tests for user management endpoints
- `test_profiles.py` - Tests for tenant and landlord profile management
- `test_properties.py` - Tests for property listing management
- `test_recommendations.py` - Tests for recommendation algorithms

## Running the Tests

### Prerequisites

Make sure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest -v
```

### Run Specific Test Files

```bash
pytest -v test_auth.py
pytest -v test_users.py
# etc.
```

## Test Database

The tests use an in-memory SQLite database via the `test_db` fixture defined in `conftest.py`. This ensures tests don't interfere with your actual database.

## Mocking

For tests involving external services (like OpenAI for image analysis and chat), consider implementing mocks to avoid actual API calls during testing.

## Adding New Tests

When adding new tests:

1. Follow the existing pattern of creating fixtures for required test data
2. Organize tests by endpoint/functionality
3. Make sure to test both successful and failing scenarios
4. If testing permissions, verify both authorized and unauthorized access

## Understanding Test Failures

If tests fail, the error message will show:
- The expected result
- The actual result
- The line of code where the test failed

Use this information to debug issues in your code.