# Technology Stack

**Analysis Date:** 2026-01-19

## Languages

**Primary:**
- Python 3.11 - Backend application, API, all business logic

**Secondary:**
- SQL - Database queries via SQLAlchemy ORM
- YAML - Configuration files (docker-compose, GitHub workflows)

## Runtime

**Environment:**
- Python 3.11 (specified in `Dockerfile`)
- Docker containers for production deployment

**Package Manager:**
- pip
- Lockfile: Not present (uses `requirements.txt` with version ranges)

## Frameworks

**Core:**
- FastAPI >=0.115.0 - Web framework, async REST API (`app/main.py`)
- Pydantic >=2.9.0 - Data validation and settings (`app/config.py`, `app/schemas/`)
- Pydantic-Settings >=2.6.0 - Environment configuration (`app/config.py`)

**Database:**
- SQLAlchemy[asyncio] >=2.0.36 - Async ORM (`app/db/base.py`, `app/models/`)
- Alembic >=1.14.0 - Database migrations (`alembic/`)

**Async/WebSocket:**
- Uvicorn[standard] >=0.32.0 - ASGI server
- websockets >=13.0 - WebSocket support
- python-socketio >=5.11.0 - Socket.IO support

**HTTP Clients:**
- httpx >=0.28.0 - Async HTTP client
- aiohttp >=3.11.0 - Async HTTP client/server

**Testing:**
- pytest >=8.3.0 - Test framework
- pytest-asyncio >=0.24.0 - Async test support
- pytest-cov >=6.0.0 - Coverage reporting
- faker >=33.1.0 - Test data generation

**Build/Dev:**
- black >=24.10.0 - Code formatting
- flake8 >=7.1.0 - Linting
- mypy >=1.14.0 - Type checking
- isort >=5.13.0 - Import sorting
- pre-commit >=4.0.0 - Git hooks

## Key Dependencies

**Critical:**
- `asyncpg` >=0.30.0 - PostgreSQL async driver (production database)
- `redis` >=5.2.0 - Redis client for caching and pub/sub (`app/websocket/manager.py`)
- `elasticsearch[async]` >=8.17.0 - Elasticsearch async client for SIEM data

**Security:**
- `python-jose[cryptography]` >=3.3.0 - JWT token handling (`app/core/security.py`)
- `passlib[bcrypt]` >=1.7.4 - Password hashing (`app/core/security.py`)
- `cryptography` >=44.0.0 - Cryptographic operations

**Security Scanning:**
- `bandit` >=1.8.0 - Python security linter
- `safety` >=3.2.0 - Dependency vulnerability scanner

**Threat Intelligence:**
- `mitreattack-python` >=5.3.0 - MITRE ATT&CK framework (`app/api/v1/mitre_attack.py`)
- `stix2` >=3.0.1 - STIX 2.1 threat intel format

**Utilities:**
- `orjson` >=3.10.0 - Fast JSON serialization
- `structlog` >=24.4.0 - Structured logging
- `prometheus-client` >=0.21.0 - Metrics export

## Configuration

**Environment:**
- Configuration via environment variables
- Pydantic Settings loads from `.env` file (`app/config.py`)
- Example config: `.env.example` (94 lines)

**Key configs required:**
- `DATABASE_URL` - PostgreSQL async connection string
- `REDIS_URL` - Redis connection URL
- `ELASTICSEARCH_URL` - Elasticsearch endpoint
- `SECRET_KEY` - JWT signing key
- `ELASTICSEARCH_PASSWORD` - Elastic authentication

**Build:**
- `Dockerfile` - Python 3.11-slim base image
- `docker-compose.yml` - Full stack orchestration
- `alembic.ini` - Migration configuration

## Platform Requirements

**Development:**
- Python 3.11+
- Docker and Docker Compose (optional for local services)
- PostgreSQL 16 with TimescaleDB extension
- Redis 7
- Elasticsearch 8.15

**Production:**
- Docker-based deployment
- Exposes port 8000 for API
- Requires PostgreSQL, Redis, Elasticsearch services
- 4 Uvicorn workers (configurable via `WORKERS` env var)

## Database Details

**Primary Database:**
- PostgreSQL 16 with TimescaleDB extension
- Async driver: `asyncpg`
- Connection pooling: 20 pool size, 10 max overflow
- ORM: SQLAlchemy 2.0 async mode

**Data Types Used:**
- JSONB for flexible schema storage (alerts, observables, MITRE mappings)
- Standard types for structured data

**Migrations:**
- Alembic with async support (`alembic/env.py`)
- Migration scripts in `alembic/versions/`

## Caching Layer

**Redis:**
- Version: 7 (Alpine image)
- Uses: WebSocket pub/sub, session caching
- Client: `redis.asyncio.Redis`
- Channels: `soc:alerts`, `soc:incidents`, `soc:dashboard`

## Search/Analytics

**Elasticsearch:**
- Version: 8.15.0
- Security: X-Pack enabled with authentication
- Index prefix: `corerecon-soc`
- Used for: Log storage, SIEM integration, search

---

*Stack analysis: 2026-01-19*
