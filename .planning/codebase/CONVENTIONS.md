# Coding Conventions

**Analysis Date:** 2026-01-19

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `detection_rule.py`, `mitre_attack.py`)
- Single-concept modules preferred (one model per file, one router per domain)

**Functions:**
- `snake_case` for all functions and methods
- Async functions prefixed with nothing special (e.g., `async def list_alerts()`)
- Private methods prefixed with underscore (e.g., `_calculate_correlation_score()`)
- Descriptive verb-noun patterns (e.g., `get_current_user()`, `create_access_token()`)

**Variables:**
- `snake_case` for all variables
- Clear, descriptive names (e.g., `alert_data`, `token_data`, `existing_query`)
- Query objects suffixed with `_query`, results with `_result` (e.g., `username_query`, `username_result`)

**Classes:**
- `PascalCase` for all classes
- Models: Singular nouns (e.g., `Alert`, `Incident`, `User`)
- Schemas: Suffixed by purpose (e.g., `AlertCreate`, `AlertUpdate`, `AlertResponse`, `AlertListResponse`)
- Services: Suffixed with `Service` (e.g., `AlertCorrelationService`, `AlertDeduplicationService`)
- Exceptions: Suffixed with `Error` or `Exception` (e.g., `ResourceNotFoundError`, `CoreReconException`)

**Constants:**
- Database table names: `snake_case` plural (e.g., `"alerts"`, `"incidents"`, `"playbook_executions"`)
- Enum-like strings: lowercase with underscores (e.g., `"new"`, `"acknowledged"`, `"false_positive"`)

## Code Style

**Formatting:**
- Tool: `black` (version 24.10.0+)
- Line length: 88 characters (black default)
- String quotes: Double quotes for docstrings, double quotes for strings

**Linting:**
- Tools: `flake8` (7.1.0+), `mypy` (1.14.0+), `isort` (5.13.0+)
- No explicit config files detected - use tool defaults
- Type hints used throughout (Optional, List, Dict, Annotated)

**Pre-commit:**
- Tool: `pre-commit` (4.0.0+) listed in requirements but no `.pre-commit-config.yaml` detected

## Import Organization

**Order:**
1. Standard library imports (datetime, typing, hashlib, json, logging)
2. Third-party imports (fastapi, sqlalchemy, pydantic, redis)
3. Local application imports (app.config, app.models, app.schemas)

**Example pattern from `app/api/v1/alerts.py`:**
```python
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertListResponse
```

**Path Aliases:**
- None configured - use relative imports from `app` package root

## Type Hints

**Usage:**
- Required on all function parameters and return types
- Use `Optional[T]` for nullable parameters
- Use `Annotated` for FastAPI dependencies
- Use `list[T]` (Python 3.9+ style) in schemas, `List[T]` in some modules

**Example:**
```python
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
```

## Error Handling

**Custom Exception Hierarchy:**
```python
# Base exception in app/core/exceptions.py
class CoreReconException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

# Domain-specific exceptions
class AuthenticationError(CoreReconException):  # 401
class AuthorizationError(CoreReconException):   # 403
class ResourceNotFoundError(CoreReconException): # 404
class ValidationError(CoreReconException):       # 422
class DatabaseError(CoreReconException):         # 500
class ExternalServiceError(CoreReconException):  # 502

# Entity-specific exceptions
class AlertNotFoundError(ResourceNotFoundError)
class IncidentNotFoundError(ResourceNotFoundError)
```

**HTTP Exception Pattern in API Endpoints:**
```python
if not alert:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Alert with ID {alert_id} not found"
    )
```

**Database Error Handling:**
```python
async with async_session_factory() as session:
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

## Logging

**Framework:** Standard library `logging`

**Setup pattern:**
```python
import logging
logger = logging.getLogger(__name__)
```

**Log levels used:**
- `logger.info()` - Successful operations (e.g., "Created alert from Elastic SIEM")
- `logger.warning()` - Non-critical issues (e.g., "Webhook secret not configured")
- `logger.error()` - Failures (e.g., "Error broadcasting to WebSocket")

**Message format:**
- Include context in message (e.g., `f"Created alert from Elastic SIEM: {alert.alert_id}"`)
- Use emoji prefixes for startup/connection status (e.g., `"Redis connection established"`, `"Failed to connect to Redis"`)

## Docstrings

**Style:** Google-style docstrings

**Function docstring pattern:**
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Token payload data
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
```

**API endpoint docstring pattern:**
```python
@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get alert by ID.

    Args:
        alert_id: Alert database ID
        db: Database session

    Returns:
        Alert details

    Raises:
        HTTPException: 404 if alert not found
    """
```

**Class/Model docstrings:**
```python
class Alert(Base):
    """Security alert model."""
```

## Function Design

**Size:**
- Functions typically 10-40 lines
- Longer functions broken into helper methods (see `_calculate_correlation_score()`, `_extract_source_ip()`)

**Parameters:**
- Use FastAPI `Query()` for query parameters with validation
- Use `Depends()` for dependency injection
- Default values provided where sensible

**Return Values:**
- API endpoints return Pydantic models or dicts
- Services return domain objects or None
- Use `scalar_one_or_none()` for single-record queries

## Module Design

**API Router Pattern:**
```python
# app/api/v1/alerts.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def list_alerts(...):
    ...
```

**Registration in main.py:**
```python
from app.api.v1 import alerts, incidents, auth
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
```

**Model Pattern:**
```python
# app/models/alert.py
from app.db.base import Base

class Alert(Base):
    __tablename__ = "alerts"
    # Column definitions...
```

**Schema Pattern:**
```python
# app/schemas/alert.py
class AlertBase(BaseModel):  # Shared fields
class AlertCreate(AlertBase):  # Creation payload
class AlertUpdate(BaseModel):  # Partial update payload
class AlertResponse(AlertBase):  # Response with all fields
    model_config = ConfigDict(from_attributes=True)
class AlertListResponse(BaseModel):  # Paginated list wrapper
```

**Service Pattern:**
```python
# app/services/correlation.py
class AlertCorrelationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_correlated_alerts(self, alert: Alert, ...) -> List[Alert]:
        ...
```

## Database Conventions

**SQLAlchemy Model Columns:**
```python
id = Column(Integer, primary_key=True, index=True)
alert_id = Column(String(255), unique=True, nullable=False, index=True)
severity = Column(
    String(20),
    nullable=False,
    index=True,
    comment="critical, high, medium, low, informational"
)
created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
raw_event = Column(JSONB, comment="Original event data")
```

**Timestamp fields:**
- `created_at` - Always present, default `datetime.utcnow`
- `updated_at` - Always present, `onupdate=datetime.utcnow`
- Domain-specific timestamps (e.g., `detected_at`, `acknowledged_at`, `resolved_at`)

**Async Query Pattern:**
```python
query = select(Alert).where(Alert.id == alert_id)
result = await db.execute(query)
alert = result.scalar_one_or_none()
```

## Pydantic Conventions

**Field validation:**
```python
title: str = Field(..., max_length=255)
severity: str = Field(..., pattern="^(critical|high|medium|low|informational)$")
page: int = Query(1, ge=1, description="Page number")
```

**ORM mode:**
```python
class AlertResponse(AlertBase):
    model_config = ConfigDict(from_attributes=True)
```

**Model conversion:**
```python
alert = Alert(**alert_data.model_dump())
update_data = alert_update.model_dump(exclude_unset=True)
```

---

*Convention analysis: 2026-01-19*
