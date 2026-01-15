# CoreRecon SOC - Development Guide

## Phase 1 Implementation Status ✅

**Phase 1 (Weeks 1-4): Core Platform** - COMPLETED

### Completed Features

#### Backend (FastAPI)
- ✅ FastAPI application with async/await support
- ✅ Configuration management with Pydantic Settings
- ✅ JWT authentication and password hashing (passlib + bcrypt)
- ✅ Custom exception handling
- ✅ Application lifecycle events (startup/shutdown)
- ✅ CORS middleware configuration
- ✅ Health check endpoint

#### Database Layer
- ✅ PostgreSQL async engine (SQLAlchemy 2.0 + AsyncPG)
- ✅ Database session management with dependency injection
- ✅ Alembic migrations configuration
- ✅ Declarative Base for ORM models

#### Data Models
- ✅ User model (authentication, roles, RBAC)
- ✅ Alert model (security alerts with MITRE ATT&CK mapping)
- ✅ Incident model (full lifecycle tracking)
- ✅ IncidentTimeline model (audit trail)
- ✅ AffectedAsset model (asset tracking)
- ✅ Observable model (IOCs with TLP classification)
- ✅ Evidence model (chain of custody)

#### API Endpoints
- ✅ Alert CRUD operations:
  - `GET /api/v1/alerts` - List with pagination and filtering
  - `GET /api/v1/alerts/{id}` - Get alert details
  - `POST /api/v1/alerts` - Create new alert
  - `PATCH /api/v1/alerts/{id}` - Update alert
  - `POST /api/v1/alerts/{id}/acknowledge` - Acknowledge alert
  - `DELETE /api/v1/alerts/{id}` - Delete alert

#### Validation Schemas
- ✅ Alert schemas (Create, Update, Response, List)
- ✅ Incident schemas (Create, Update, Response, List)
- ✅ User schemas (Create, Update, Response, Token)

## Getting Started

### Prerequisites

Ensure you have the following installed:
- Python 3.11+
- PostgreSQL 14+
- Redis 7+ (for Phase 2 WebSocket support)
- Node.js 20+ (for frontend development)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/realmarauder/CoreRecon_SOC.git
cd CoreRecon_SOC
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and configure:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://soc_user:your_password@localhost:5432/soc_db

# Security
SECRET_KEY=$(openssl rand -hex 32)  # Generate secure key

# Redis (for Phase 2)
REDIS_URL=redis://localhost:6379/0
```

5. **Create PostgreSQL database:**
```bash
createdb soc_db
createuser soc_user
psql -c "ALTER USER soc_user WITH PASSWORD 'your_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE soc_db TO soc_user;"
```

6. **Run database migrations:**
```bash
alembic upgrade head
```

7. **Start the development server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Access the API:**
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Project Structure

```
CoreRecon_SOC/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration management
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── alerts.py            # ✅ Alert endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── events.py                # ✅ Lifecycle events
│   │   ├── security.py              # ✅ JWT & password hashing
│   │   └── exceptions.py            # ✅ Custom exceptions
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── base.py                  # ✅ Database engine & session
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                  # ✅ User model
│   │   ├── alert.py                 # ✅ Alert model
│   │   ├── incident.py              # ✅ Incident models
│   │   ├── observable.py            # ✅ Observable/IOC model
│   │   └── evidence.py              # ✅ Evidence model
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── alert.py                 # ✅ Alert schemas
│       ├── incident.py              # ✅ Incident schemas
│       └── user.py                  # ✅ User schemas
│
├── alembic/
│   ├── env.py                       # ✅ Migration environment
│   └── versions/                    # Migration files
│
├── tests/                           # 📋 To be implemented
├── frontend/                        # 📋 To be implemented
├── docker-compose.yml               # ✅ Multi-service deployment
├── Dockerfile                       # ✅ Backend container
└── requirements.txt                 # ✅ Python dependencies
```

## API Usage Examples

### Create an Alert

```bash
curl -X POST http://localhost:8000/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "ALERT-2026-001",
    "title": "Suspicious PowerShell Execution",
    "description": "PowerShell executed with encoded command",
    "severity": "high",
    "source": "EDR",
    "detection_rule_name": "Suspicious PowerShell Activity",
    "mitre_tactics": {"tactic": "Execution"},
    "mitre_techniques": [{"id": "T1059.001", "name": "PowerShell"}]
  }'
```

### List Alerts with Filtering

```bash
# Get all critical alerts
curl "http://localhost:8000/api/v1/alerts?severity=critical&page=1&page_size=25"

# Get acknowledged alerts
curl "http://localhost:8000/api/v1/alerts?status=acknowledged"
```

### Acknowledge an Alert

```bash
curl -X POST http://localhost:8000/api/v1/alerts/1/acknowledge
```

## Docker Deployment

### Start all services:

```bash
docker-compose up -d
```

This starts:
- PostgreSQL with TimescaleDB
- Redis
- Elasticsearch + Kibana
- FastAPI backend
- React frontend (when implemented)

### Check service status:

```bash
docker-compose ps
```

### View logs:

```bash
docker-compose logs -f backend
```

## Database Management

### Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations:

```bash
alembic upgrade head
```

### Rollback migration:

```bash
alembic downgrade -1
```

### View migration history:

```bash
alembic history
```

## Testing

### Run all tests:

```bash
pytest tests/ -v
```

### Run with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

### Run specific test file:

```bash
pytest tests/test_api/test_alerts.py -v
```

## Next Steps - Phase 2 (Weeks 5-6)

### Upcoming Features
- 📋 Incident CRUD API endpoints
- 📋 Authentication API endpoints (login, refresh, logout)
- 📋 WebSocket manager for real-time alerts
- 📋 Redis pub/sub integration
- 📋 Elastic SIEM webhook integration
- 📋 Alert ingestion and normalization
- 📋 Detection rule management
- 📋 Basic correlation engine

### Frontend Development
- 📋 React 18+ with TypeScript setup
- 📋 Material-UI v5 components
- 📋 Dashboard layout with navigation
- 📋 Alert list and detail views
- 📋 Real-time WebSocket integration

## Troubleshooting

### Database connection issues:

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
psql -U soc_user -d soc_db -h localhost
```

### Migration errors:

```bash
# Reset database (WARNING: Destroys all data)
alembic downgrade base
alembic upgrade head
```

### Port already in use:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, code style, and pull request process.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)

---

**Last Updated**: January 15, 2026
**Version**: 1.0.0 - Phase 1
**Status**: ✅ Phase 1 Complete, 📋 Phase 2 In Progress
