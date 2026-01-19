# Codebase Structure

**Analysis Date:** 2026-01-19

## Directory Layout

```
CoreRecon_SOC/
├── app/                    # Main application package
│   ├── api/               # REST API layer
│   │   └── v1/            # API version 1 endpoints
│   ├── core/              # Cross-cutting utilities
│   ├── db/                # Database configuration
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic validation schemas
│   ├── services/          # Business logic services
│   ├── websocket/         # WebSocket handlers and manager
│   ├── __init__.py
│   ├── config.py          # Application settings
│   └── main.py            # FastAPI application entry point
├── alembic/               # Database migrations
├── docs/                  # Documentation
├── .github/               # GitHub workflows and templates
├── .planning/             # GSD planning documents
│   └── codebase/          # Codebase analysis documents
├── docker-compose.yml     # Container orchestration
├── Dockerfile             # Application container build
├── requirements.txt       # Python dependencies
├── alembic.ini            # Migration configuration
└── .env.example           # Environment variable template
```

## Directory Purposes

**`app/`:**
- Purpose: Main application source code
- Contains: All Python modules for the API
- Key files: `main.py` (entry), `config.py` (settings)

**`app/api/v1/`:**
- Purpose: REST API endpoint handlers
- Contains: FastAPI routers with endpoint functions
- Key files:
  - `alerts.py` - Alert CRUD operations
  - `incidents.py` - Incident management with SLA tracking
  - `auth.py` - User authentication (login, register, token refresh)
  - `webhooks.py` - SIEM integration endpoints
  - `dashboard.py` - Metrics and KPI endpoints
  - `playbooks.py` - Playbook management and execution
  - `detection_rules.py` - Detection rule CRUD and tuning
  - `mitre_attack.py` - MITRE ATT&CK Navigator integration
  - `correlation.py` - Alert correlation and deduplication

**`app/core/`:**
- Purpose: Shared utilities and cross-cutting concerns
- Contains: Security, events, exceptions
- Key files:
  - `security.py` - JWT token creation/validation, password hashing
  - `events.py` - Application lifecycle (DB connect/disconnect)
  - `exceptions.py` - Custom exception hierarchy

**`app/db/`:**
- Purpose: Database connection and session management
- Contains: SQLAlchemy engine, session factory, base class
- Key files:
  - `base.py` - Engine config, `get_db()` dependency, declarative `Base`

**`app/models/`:**
- Purpose: SQLAlchemy ORM entity definitions
- Contains: Database table models with relationships
- Key files:
  - `alert.py` - Alert model (security events from SIEMs)
  - `incident.py` - Incident, IncidentTimeline, AffectedAsset models
  - `user.py` - User account model
  - `playbook.py` - Playbook, PlaybookExecution models
  - `detection_rule.py` - DetectionRule, RuleTuning models
  - `observable.py` - Observable (IOC) model
  - `evidence.py` - Evidence attachment model
  - `threat_intel.py` - Threat intelligence model

**`app/schemas/`:**
- Purpose: Pydantic models for API validation
- Contains: Request/response schemas per domain
- Key files:
  - `alert.py` - AlertCreate, AlertUpdate, AlertResponse, AlertListResponse
  - `incident.py` - IncidentCreate, IncidentUpdate, IncidentResponse
  - `user.py` - UserCreate, UserResponse, Token
  - `playbook.py` - Playbook and execution schemas
  - `detection_rule.py` - Rule and tuning schemas

**`app/services/`:**
- Purpose: Business logic and domain services
- Contains: Service classes with complex operations
- Key files:
  - `correlation.py` - AlertCorrelationService, AlertDeduplicationService

**`app/websocket/`:**
- Purpose: Real-time WebSocket communication
- Contains: Connection manager and endpoint handlers
- Key files:
  - `manager.py` - WebSocketManager (singleton, Redis pub/sub support)
  - `handlers.py` - WebSocket endpoint routes

**`alembic/`:**
- Purpose: Database schema migrations
- Contains: Migration scripts, env configuration
- Key files: `env.py` (migration runtime config)

## Key File Locations

**Entry Points:**
- `app/main.py`: FastAPI application, router registration, lifespan events

**Configuration:**
- `app/config.py`: Pydantic Settings class, environment variable mapping
- `.env.example`: Template for required environment variables
- `alembic.ini`: Database migration configuration
- `docker-compose.yml`: Container service definitions

**Core Logic:**
- `app/api/v1/alerts.py`: Alert CRUD with pagination and filtering
- `app/api/v1/incidents.py`: Incident workflow with SLA tracking
- `app/services/correlation.py`: Alert correlation scoring and deduplication
- `app/websocket/manager.py`: Real-time event distribution

**Testing:**
- No test directory exists currently (tests not implemented)

## Naming Conventions

**Files:**
- Snake_case for all Python files: `detection_rules.py`, `mitre_attack.py`
- Singular names for models: `alert.py`, `incident.py`, `user.py`
- Plural or descriptive for API routes: `alerts.py`, `webhooks.py`

**Directories:**
- Lowercase, no separators: `api`, `core`, `models`, `schemas`
- Version prefix for API: `v1`

**Python Classes:**
- PascalCase: `AlertCorrelationService`, `WebSocketManager`
- Model suffix for ORM: `Alert`, `Incident`, `User`
- Schema suffix pattern: `AlertCreate`, `AlertResponse`, `AlertListResponse`

**Python Functions:**
- snake_case: `get_current_user`, `create_access_token`
- Async functions prefixed with `async def`
- CRUD pattern: `list_*`, `get_*`, `create_*`, `update_*`, `delete_*`

**Database Tables:**
- Plural lowercase with underscores: `alerts`, `incidents`, `playbook_executions`

## Where to Add New Code

**New API Endpoint:**
- Create router in `app/api/v1/{resource}.py`
- Register in `app/main.py` with `app.include_router()`
- Add schema in `app/schemas/{resource}.py`
- Add model in `app/models/{resource}.py` if new entity

**New Model:**
- Create file `app/models/{entity}.py`
- Import model class in `app/models/__init__.py`
- Create Alembic migration for table

**New Schema:**
- Create file `app/schemas/{entity}.py`
- Follow pattern: `{Entity}Base`, `{Entity}Create`, `{Entity}Update`, `{Entity}Response`
- Import in `app/schemas/__init__.py`

**New Service:**
- Create file `app/services/{domain}.py`
- Service class takes `db: AsyncSession` in constructor
- Import and use in API endpoint

**New WebSocket Channel:**
- Add channel to `WebSocketManager.active_connections` dict in `app/websocket/manager.py`
- Create handler in `app/websocket/handlers.py`
- Add broadcast method to manager

**Utilities:**
- Cross-cutting: `app/core/{utility}.py`
- Domain-specific: `app/services/{domain}.py`

## Special Directories

**`.planning/`:**
- Purpose: GSD command planning documents and codebase analysis
- Generated: By GSD commands
- Committed: Yes (documentation)

**`.github/`:**
- Purpose: GitHub Actions workflows and issue templates
- Generated: No (manually maintained)
- Committed: Yes

**`alembic/`:**
- Purpose: Database migration scripts
- Generated: Via `alembic revision` command
- Committed: Yes (schema versioning)

**`docs/`:**
- Purpose: Project documentation
- Contains: Architecture docs, contributing guide, project plan
- Committed: Yes

---

*Structure analysis: 2026-01-19*
