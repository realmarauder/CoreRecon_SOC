# Architecture

**Analysis Date:** 2026-01-19

## Pattern Overview

**Overall:** Layered Monolith with Domain-Driven Design

**Key Characteristics:**
- FastAPI async REST API with WebSocket support
- SQLAlchemy ORM with PostgreSQL (async)
- Clear separation: API routes, services, models, schemas
- Dependency injection via FastAPI's Depends system
- Event-driven real-time updates via WebSocket + Redis pub/sub

## Layers

**Presentation Layer (API):**
- Purpose: HTTP request handling, routing, validation
- Location: `app/api/v1/`
- Contains: FastAPI routers with endpoint handlers
- Depends on: Services, Schemas, Models, Database session
- Used by: External clients (REST/WebSocket)

**Service Layer:**
- Purpose: Business logic, complex operations
- Location: `app/services/`
- Contains: Domain services (correlation, deduplication)
- Depends on: Models, Database session
- Used by: API endpoints
- Example: `app/services/correlation.py` - `AlertCorrelationService`, `AlertDeduplicationService`

**Data Layer (Models):**
- Purpose: Database entity definitions and relationships
- Location: `app/models/`
- Contains: SQLAlchemy ORM models
- Depends on: Base declarative class from `app/db/base.py`
- Used by: Services, API endpoints

**Schema Layer:**
- Purpose: Request/response validation, serialization
- Location: `app/schemas/`
- Contains: Pydantic models for API contracts
- Depends on: Nothing (pure data classes)
- Used by: API endpoints for validation

**Core Layer:**
- Purpose: Cross-cutting concerns, utilities
- Location: `app/core/`
- Contains: Security (JWT), events, exceptions
- Depends on: Config
- Used by: All layers

**WebSocket Layer:**
- Purpose: Real-time bidirectional communication
- Location: `app/websocket/`
- Contains: Connection manager, endpoint handlers
- Depends on: Redis (optional), Core
- Used by: API layer (routers)

## Data Flow

**Alert Ingestion (SIEM Webhook):**

1. SIEM sends POST to `/api/v1/webhooks/{provider}` (Elastic, Sentinel, Splunk)
2. Webhook endpoint validates signature if configured
3. Payload normalized via provider-specific function (`normalize_elastic_alert()`)
4. Alert model created and committed to PostgreSQL
5. WebSocket manager broadcasts alert to connected clients
6. If Redis configured, alert published to `soc:alerts` channel for distributed instances

**Incident Management Flow:**

1. Incident created via POST `/api/v1/incidents/`
2. Ticket number generated (`INC-{YEAR}-{NNNNN}`)
3. SLA due times calculated based on severity
4. IncidentTimeline entry created for audit trail
5. Incident persisted to PostgreSQL
6. Status changes trigger timeline entries and timestamp updates

**Real-time Updates (WebSocket):**

1. Client connects to `/ws/alerts`, `/ws/incidents/{id}`, or `/ws/dashboard`
2. WebSocketManager registers connection to channel
3. On data change, API calls `manager.broadcast_{type}()`
4. Manager serializes to JSON and sends to all channel subscribers
5. If Redis enabled, also publishes for other instances

**State Management:**
- Server-side: PostgreSQL (persistent), Redis (pub/sub, caching)
- Client-side: WebSocket connections maintain session state
- Authentication state: JWT tokens (stateless)

## Key Abstractions

**Alert:**
- Purpose: Security event from SIEM/EDR sources
- Examples: `app/models/alert.py`, `app/schemas/alert.py`
- Pattern: CRUD with status workflow (new -> acknowledged -> investigating -> resolved)
- Contains: Severity, MITRE ATT&CK mapping, observables, raw event data

**Incident:**
- Purpose: Tracked security case requiring investigation
- Examples: `app/models/incident.py`, `app/schemas/incident.py`
- Pattern: Workflow with SLA tracking, timeline audit log
- Relationships: User (analyst), Alerts (source), PlaybookExecutions, Timeline, AffectedAssets

**Playbook:**
- Purpose: Automated response workflow template
- Examples: `app/models/playbook.py`
- Pattern: Template with steps (JSONB), execution instances track progress
- Contains: Steps, trigger conditions, approval requirements

**DetectionRule:**
- Purpose: Threat detection rule (Sigma, YARA, custom)
- Examples: `app/models/detection_rule.py`
- Pattern: Versioned rule with deployment tracking and tuning history

**WebSocketManager:**
- Purpose: Singleton managing all WebSocket connections
- Examples: `app/websocket/manager.py`
- Pattern: Channel-based pub/sub with optional Redis backing
- Channels: `alerts`, `incidents`, `dashboard`, `incident_{id}`

## Entry Points

**Application Entry:**
- Location: `app/main.py`
- Triggers: `uvicorn` server start
- Responsibilities: FastAPI app creation, middleware config, router registration, lifespan events

**API Routers:**
- Location: `app/api/v1/*.py`
- Triggers: HTTP requests to `/api/v1/*`
- Responsibilities: Request validation, handler execution, response serialization

**WebSocket Endpoints:**
- Location: `app/websocket/handlers.py`
- Triggers: WebSocket upgrade requests to `/ws/*`
- Responsibilities: Connection management, message routing, heartbeat

**Webhooks:**
- Location: `app/api/v1/webhooks.py`
- Triggers: POST from external SIEMs (Elastic, Sentinel, Splunk)
- Responsibilities: Signature verification, payload normalization, alert creation

## Error Handling

**Strategy:** Exception hierarchy with HTTP status mapping

**Patterns:**
- Custom exception classes in `app/core/exceptions.py`
- Base `CoreReconException` with message and status_code
- Domain-specific exceptions: `AlertNotFoundError`, `IncidentNotFoundError`
- FastAPI `HTTPException` for API-level errors
- Try/except with rollback in database operations (see `app/db/base.py` get_db)

**Exception Hierarchy:**
```
CoreReconException (base, 500)
  AuthenticationError (401)
  AuthorizationError (403)
  ResourceNotFoundError (404)
    AlertNotFoundError
    IncidentNotFoundError
  ValidationError (422)
  DatabaseError (500)
  ExternalServiceError (502)
```

## Cross-Cutting Concerns

**Logging:**
- Standard library `logging` module
- Logger per module: `logger = logging.getLogger(__name__)`
- Log level configurable via `LOG_LEVEL` env var

**Validation:**
- Pydantic schemas for request/response validation
- Field validators (patterns, ranges) in schemas
- SQLAlchemy column constraints (nullable, unique, index)

**Authentication:**
- JWT tokens via `python-jose`
- OAuth2 password flow for login
- Token decode in `app/core/security.py`
- `get_current_user` dependency for protected routes
- Password hashing with bcrypt via `passlib`

**Configuration:**
- Pydantic Settings in `app/config.py`
- Environment variables with `.env` file support
- Cached global `settings` singleton

**Database Sessions:**
- Async sessions via `get_db()` dependency
- Auto-commit on success, rollback on exception
- Connection pooling configured in `app/db/base.py`

---

*Architecture analysis: 2026-01-19*
