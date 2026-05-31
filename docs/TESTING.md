# Testing Guide

## Overview

This guide explains how to run tests for the Pre-Visit Voice Agent API.

The test suite includes:
- ✅ **Unit Tests** - Test individual components
- ✅ **Integration Tests** - Test API endpoints
- ✅ **Database Tests** - Test CRUD operations
- ✅ **Error Handling Tests** - Test edge cases

**Total Tests: 50+**
**Coverage Target: >80%**

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Testing dependencies:
- `pytest` - Test framework
- `pytest-cov` - Code coverage
- `pytest-mock` - Mocking utilities
- `pytest-flask` - Flask testing utilities

### 2. Verify Installation

```bash
pytest --version
# pytest 7.4.3
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests with verbose output
pytest -v

# Run all tests with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test class
pytest tests/test_api.py::TestSessionManagement -v

# Run specific test
pytest tests/test_api.py::TestSessionManagement::test_create_session_success -v
```

### Run Tests by Category

```bash
# Health and info endpoints
pytest tests/test_api.py::TestHealthAndInfo -v

# Session management
pytest tests/test_api.py::TestSessionManagement -v

# Message management
pytest tests/test_api.py::TestMessageManagement -v

# Clinical data
pytest tests/test_api.py::TestClinicalData -v

# Export functionality
pytest tests/test_api.py::TestExport -v

# Error handling
pytest tests/test_api.py::TestErrorHandling -v

# Database operations
pytest tests/test_api.py::TestDatabaseOperations -v

# Integration tests
pytest tests/test_api.py::TestIntegration -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=. --cov-report=html
# Open: htmlcov/index.html

# Generate XML coverage report (for CI/CD)
pytest --cov=. --cov-report=xml

# Show coverage for specific file
pytest --cov=api --cov-report=term-missing tests/
```

### Run with Additional Options

```bash
# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run last failed tests
pytest --lf

# Run failed then others
pytest --ff

# Show local variables on failure
pytest -l

# Run tests matching pattern
pytest -k "session" -v
```

---

## Test Structure

### File Organization

```
Pre-Visit-real-time-voice-agent/
├── tests/
│   ├── __init__.py
│   ├── test_api.py           # Main API tests (50+ tests)
│   ├── conftest.py           # Pytest fixtures and configuration
│   └── test_migrations.py    # (Optional) Migration tests
├── conftest.py               # Global pytest configuration
└── requirements.txt          # Testing dependencies
```

### Conftest.py Fixtures

```python
# Available fixtures in tests:

@pytest.fixture
def db():
    """Test database (SQLite in-memory)"""
    
@pytest.fixture
def client():
    """Flask test client"""
    
@pytest.fixture
def sample_session():
    """Pre-created test session"""
    
@pytest.fixture
def sample_patient_id():
    """Sample patient ID for testing"""
```

---

## Test Categories

### 1. Health & Info Tests (2 tests)

```python
def test_health_check():
    """GET /health returns healthy status"""
    
def test_api_info():
    """GET /api/info returns API information"""
```

### 2. Session Management Tests (8 tests)

```python
def test_create_session_success():
def test_create_session_missing_patient_id():
def test_create_session_invalid_language():
def test_get_session_success():
def test_get_session_not_found():
def test_end_session_success():
def test_end_session_invalid_status():
def test_get_patient_sessions():
```

### 3. Message Management Tests (7 tests)

```python
def test_add_message_success():
def test_add_message_missing_fields():
def test_add_message_invalid_role():
def test_add_message_to_inactive_session():
def test_get_messages_success():
def test_get_messages_not_found():
```

### 4. Clinical Data Tests (3 tests)

```python
def test_save_clinical_data_success():
def test_get_clinical_data_success():
def test_get_clinical_data_not_found():
```

### 5. Export Tests (2 tests)

```python
def test_export_session_json_success():
def test_export_session_json_not_found():
```

### 6. Error Handling Tests (3 tests)

```python
def test_404_not_found():
def test_malformed_json():
def test_missing_content_type():
```

### 7. Database Tests (10 tests)

```python
def test_create_session_db():
def test_get_session_db():
def test_end_session_db():
def test_add_message_db():
def test_get_messages_db():
def test_save_clinical_data_db():
def test_export_session_json_db():
def test_health_check_db():
```

### 8. Integration Tests (1 comprehensive test)

```python
def test_full_conversation_flow():
    """Complete workflow: create session → add messages → save data → export → end"""
```

---

## Writing New Tests

### Template: Test a New Endpoint

```python
def test_my_endpoint_success(self, client):
    """Test POST /api/my/endpoint - Success case"""
    response = client.post('/api/my/endpoint', json={
        'field1': 'value1',
        'field2': 'value2'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data

def test_my_endpoint_error(self, client):
    """Test POST /api/my/endpoint - Error case"""
    response = client.post('/api/my/endpoint', json={
        'field1': 'value1'
        # Missing required field2
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
```

### Add to Test Suite

```bash
# 1. Add test method to appropriate class in test_api.py
# 2. Run new test
pytest tests/test_api.py::TestMyClass::test_my_endpoint_success -v

# 3. Verify it passes
# 4. Commit to version control
git add tests/test_api.py
git commit -m "test: add tests for my endpoint"
```

---

## Debugging Failed Tests

### 1. Run with Verbose Output

```bash
pytest tests/test_api.py::TestSessionManagement::test_create_session_success -vv
```

### 2. Show Print Statements

```bash
pytest tests/test_api.py::TestSessionManagement::test_create_session_success -s
```

### 3. Show Local Variables on Failure

```bash
pytest tests/test_api.py::TestSessionManagement::test_create_session_success -l
```

### 4. Drop into Debugger on Failure

```bash
pytest tests/test_api.py::TestSessionManagement::test_create_session_success --pdb
```

### 5. Check Test Database State

```python
def test_example(client, db):
    """Example test with database inspection"""
    response = client.post('/api/sessions', json={'patient_id': 'P123'})
    
    # Inspect database
    sessions = db.SessionLocal().query(ConversationSession).all()
    print(f"Sessions in DB: {len(sessions)}")
    
    assert response.status_code == 201
```

---

## Mocking

### Mock External Services

```python
from unittest.mock import patch

def test_api_with_mock(client):
    """Test API with mocked LLM"""
    with patch('api.llm_engine.generate_response') as mock_llm:
        mock_llm.return_value = "Mocked response"
        
        response = client.post(
            '/api/sessions/SESSION_ID/messages',
            json={'role': 'user', 'content': 'Hello', 'turn_number': 1}
        )
        
        assert response.status_code == 201
        mock_llm.assert_called_once()
```

### Mock Database

```python
def test_with_mock_db(client):
    """Test with mocked database"""
    with patch('api.db.get_session_by_id') as mock_db:
        mock_db.return_value = None
        
        response = client.get('/api/sessions/INVALID_ID')
        assert response.status_code == 404
```

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Every push to main/develop
- Every pull request

**.github/workflows/deploy.yml:**
```yaml
- name: Run tests
  run: |
    pytest --cov=. --cov-report=term-missing
```

### Pre-commit Hook (Optional)

```bash
# Create .git/hooks/pre-commit
#!/bin/bash
pytest tests/ -q
if [ $? -ne 0 ]; then
  echo "Tests failed. Commit aborted."
  exit 1
fi
```

---

## Performance Tests

### Measure Test Execution Time

```bash
pytest --durations=10

# Output shows 10 slowest tests
```

### Run Only Fast Tests

```bash
pytest -m "not slow"
```

---

## Code Coverage

### Generate Coverage Report

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing

# Open: htmlcov/index.html in browser
```

### Coverage Targets

| Module | Target |
|--------|--------|
| api.py | > 85% |
| models.py | > 90% |
| database.py | > 80% |
| Overall | > 80% |

### View Coverage for Specific File

```bash
pytest --cov=api --cov-report=term-missing tests/test_api.py
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'conftest'"

```bash
# Solution: Run pytest from root directory
cd /path/to/Pre-Visit-real-time-voice-agent
pytest tests/
```

### Issue: "Database is locked" (SQLite)

```bash
# Solution: Delete test database
rm conversations.db
pytest tests/
```

### Issue: Tests pass locally but fail in CI

```bash
# Solution: Check environment variables
export FLASK_ENV=testing
pytest tests/ -v
```

### Issue: Fixture not found

```bash
# Solution: Ensure conftest.py is in:
# 1. Root directory
# 2. tests/ directory

# Then run:
pytest --fixtures  # List all available fixtures
```

---

## Best Practices

### ✅ DO

- ✅ Write tests for all new endpoints
- ✅ Test both success and error cases
- ✅ Use fixtures for shared data
- ✅ Keep tests isolated and independent
- ✅ Use descriptive test names
- ✅ Test edge cases
- ✅ Keep tests fast (< 1 second each)

### ❌ DON'T

- ❌ Don't use real API keys in tests
- ❌ Don't make HTTP calls to external services
- ❌ Don't use real production database
- ❌ Don't have tests that depend on each other
- ❌ Don't commit test data to repository
- ❌ Don't ignore test failures

---

## Example Test Run

```bash
$ pytest tests/test_api.py -v --cov=api --cov-report=term-missing

tests/test_api.py::TestHealthAndInfo::test_health_check PASSED           [  2%]
tests/test_api.py::TestHealthAndInfo::test_api_info PASSED               [  4%]
tests/test_api.py::TestSessionManagement::test_create_session_success PASSED [ 6%]
tests/test_api.py::TestSessionManagement::test_create_session_missing_patient_id PASSED [ 8%]
... [43 more tests] ...

======================== 50 passed in 2.34s ========================

Name                    Stmts   Miss  Cover   Missing
────────────────────────────────────────────────
api.py                    156     12    92%    145-157
models.py                 142      8    94%    120-128
database.py               198     15    92%    234-248
────────────────────────────────────────────────
TOTAL                     496     35    93%
```

---

## Quick Reference

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test
pytest tests/test_api.py::TestSessionManagement::test_create_session_success

# Stop on first failure
pytest -x

# Show output
pytest -s

# Verbose output
pytest -v

# Generate HTML report
pytest --cov=. --cov-report=html

# Run and generate XML (for CI)
pytest --cov=. --cov-report=xml
```

---

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/7.x/how-to/fixtures.html)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/faq/orm.html#how-do-i-test-a-query-or-orm-relationship)
