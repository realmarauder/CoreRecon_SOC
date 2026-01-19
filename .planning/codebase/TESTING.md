# Testing Patterns

**Analysis Date:** 2026-01-19

## Test Framework

**Runner:**
- `pytest` (8.3.0+)
- `pytest-asyncio` (0.24.0+) for async test support
- Config: No `pytest.ini` or `pyproject.toml` test config detected

**Assertion Library:**
- pytest native assertions

**Coverage:**
- `pytest-cov` (6.0.0+)

**Run Commands:**
```bash
pytest tests/ -v              # Run all tests with verbose output
pytest tests/ --cov=app       # Run with coverage
pytest tests/ --cov=app --cov-report=html  # Coverage with HTML report
```

## Test Status

**Current State: NO TESTS IMPLEMENTED**

The `tests/` directory is listed in `DEVELOPMENT.md` as "To be implemented". No test files, conftest.py, or test configurations exist.

## Recommended Test File Organization

Based on the codebase structure, use this test layout:

**Location:**
- Co-located tests discouraged - use separate `tests/` directory
- Mirror `app/` structure in `tests/`

**Naming:**
- Test files: `test_{module}.py`
- Test functions: `test_{function_name}_{scenario}`

**Recommended Structure:**
```
tests/
├── conftest.py                    # Shared fixtures
├── test_api/
│   └── test_v1/
│       ├── test_alerts.py         # Tests for app/api/v1/alerts.py
│       ├── test_incidents.py      # Tests for app/api/v1/incidents.py
│       ├── test_auth.py           # Tests for app/api/v1/auth.py
│       ├── test_webhooks.py       # Tests for app/api/v1/webhooks.py
│       ├── test_playbooks.py      # Tests for app/api/v1/playbooks.py
│       └── test_correlation.py    # Tests for app/api/v1/correlation.py
├── test_core/
│   ├── test_security.py           # Tests for app/core/security.py
│   └── test_exceptions.py         # Tests for app/core/exceptions.py
├── test_services/
│   └── test_correlation.py        # Tests for app/services/correlation.py
└── test_websocket/
    └── test_manager.py            # Tests for app/websocket/manager.py
```

## Recommended Test Patterns

**Conftest.py Setup:**
```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from faker import Faker

from app.main import app
from app.db.base import Base, get_db

fake = Faker()

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_soc_db"

@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(async_engine):
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

**API Endpoint Test Pattern:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_alerts_empty(client: AsyncClient):
    """Test listing alerts when database is empty."""
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0

@pytest.mark.asyncio
async def test_create_alert_success(client: AsyncClient):
    """Test creating a new alert."""
    alert_data = {
        "alert_id": "ALERT-TEST-001",
        "title": "Test Alert",
        "severity": "high",
        "source": "Test"
    }
    response = await client.post("/api/v1/alerts", json=alert_data)
    assert response.status_code == 201
    data = response.json()
    assert data["alert_id"] == "ALERT-TEST-001"
    assert data["status"] == "new"

@pytest.mark.asyncio
async def test_create_alert_duplicate(client: AsyncClient):
    """Test creating alert with duplicate alert_id fails."""
    alert_data = {
        "alert_id": "ALERT-DUP-001",
        "title": "Duplicate Test",
        "severity": "medium"
    }
    # Create first
    await client.post("/api/v1/alerts", json=alert_data)
    # Try duplicate
    response = await client.post("/api/v1/alerts", json=alert_data)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_get_alert_not_found(client: AsyncClient):
    """Test getting non-existent alert returns 404."""
    response = await client.get("/api/v1/alerts/99999")
    assert response.status_code == 404
```

**Service Test Pattern:**
```python
import pytest
from app.services.correlation import AlertCorrelationService
from app.models.alert import Alert

@pytest.mark.asyncio
async def test_calculate_correlation_score_same_source_ip(db_session):
    """Test correlation score when alerts share source IP."""
    service = AlertCorrelationService(db_session)

    alert1 = Alert(
        alert_id="A1",
        title="Alert 1",
        severity="high",
        raw_event={"source_ip": "192.168.1.100"}
    )
    alert2 = Alert(
        alert_id="A2",
        title="Alert 2",
        severity="high",
        raw_event={"source_ip": "192.168.1.100"}
    )

    score = service._calculate_correlation_score(alert1, alert2)
    assert score >= 0.25  # Source IP match weight
```

**Authentication Test Pattern:**
```python
import pytest
from app.core.security import create_access_token, decode_token, verify_password, get_password_hash

def test_password_hash_and_verify():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_create_and_decode_token():
    """Test JWT token creation and decoding."""
    data = {"sub": "testuser", "user_id": 1}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded.username == "testuser"
    assert decoded.user_id == 1
```

## Mocking

**Framework:** pytest + unittest.mock

**Database Mocking:**
- Use test database with fixtures (recommended)
- Override `get_db` dependency in FastAPI

**External Service Mocking:**
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_redis_broadcast(client: AsyncClient):
    """Test WebSocket broadcast with mocked Redis."""
    with patch("app.websocket.manager.manager.redis_client") as mock_redis:
        mock_redis.publish = AsyncMock()
        # Test code that triggers broadcast
        mock_redis.publish.assert_called_once()
```

**What to Mock:**
- Redis connections (`app.websocket.manager.manager.redis_client`)
- External SIEM webhook responses
- Elasticsearch client calls
- Email/notification services (when implemented)

**What NOT to Mock:**
- Database queries (use test database)
- Pydantic validation
- FastAPI request/response handling
- Business logic in services

## Fixtures and Factories

**Test Data with Faker:**
```python
from faker import Faker
fake = Faker()

def create_test_alert_data():
    return {
        "alert_id": f"ALERT-{fake.uuid4()[:8]}",
        "title": fake.sentence(nb_words=5),
        "description": fake.paragraph(),
        "severity": fake.random_element(["critical", "high", "medium", "low"]),
        "source": fake.random_element(["EDR", "SIEM", "Cloud"]),
    }

def create_test_user_data():
    return {
        "username": fake.user_name(),
        "email": fake.email(),
        "full_name": fake.name(),
        "password": fake.password(length=12),
        "role": "analyst"
    }
```

**Model Factories:**
```python
@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        role="analyst",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Get auth headers for authenticated requests."""
    from app.core.security import create_access_token
    token = create_access_token({"sub": test_user.username, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}
```

**Fixture Location:**
- Shared fixtures: `tests/conftest.py`
- Domain-specific fixtures: `tests/test_api/conftest.py`

## Coverage

**Requirements:** Not enforced (no coverage threshold configured)

**View Coverage:**
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

**Recommended Coverage Targets:**
- Overall: 80%+
- Core modules (`app/core/`): 90%+
- API endpoints (`app/api/`): 85%+
- Services (`app/services/`): 85%+

## Test Types

**Unit Tests:**
- Test individual functions in isolation
- `app/core/security.py` - Token creation, password hashing
- `app/core/exceptions.py` - Exception classes
- Service helper methods (e.g., `_calculate_correlation_score`)

**Integration Tests:**
- Test API endpoints with test database
- Test WebSocket manager with mocked Redis
- Test webhook normalization functions

**E2E Tests:**
- Not configured
- Consider using `TestClient` with full app for critical flows:
  - User registration -> login -> create alert -> acknowledge
  - Webhook ingestion -> alert creation -> WebSocket broadcast

## Common Patterns

**Async Testing:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

**Error Testing:**
```python
import pytest
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_get_nonexistent_raises_404(client: AsyncClient):
    response = await client.get("/api/v1/alerts/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

**Parameterized Tests:**
```python
import pytest

@pytest.mark.parametrize("severity,expected_valid", [
    ("critical", True),
    ("high", True),
    ("medium", True),
    ("low", True),
    ("informational", True),
    ("invalid", False),
])
def test_severity_validation(severity, expected_valid):
    from pydantic import ValidationError
    from app.schemas.alert import AlertCreate

    try:
        AlertCreate(alert_id="TEST", title="Test", severity=severity)
        assert expected_valid is True
    except ValidationError:
        assert expected_valid is False
```

## Priority Test Cases

**High Priority (implement first):**
1. Authentication flow (`app/api/v1/auth.py`)
   - Login with valid/invalid credentials
   - Token refresh
   - Protected endpoint access

2. Alert CRUD (`app/api/v1/alerts.py`)
   - Create, read, update, delete
   - Pagination and filtering
   - Duplicate prevention

3. Incident CRUD (`app/api/v1/incidents.py`)
   - Lifecycle transitions
   - SLA calculation
   - Timeline entries

**Medium Priority:**
4. Webhook ingestion (`app/api/v1/webhooks.py`)
   - Elastic, Sentinel, Splunk normalization
   - Signature verification

5. Correlation service (`app/services/correlation.py`)
   - Score calculation
   - Deduplication logic

**Lower Priority:**
6. WebSocket manager (`app/websocket/manager.py`)
7. Playbook execution (`app/api/v1/playbooks.py`)
8. Detection rules (`app/api/v1/detection_rules.py`)

---

*Testing analysis: 2026-01-19*
