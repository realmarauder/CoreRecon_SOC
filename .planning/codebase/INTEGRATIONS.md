# External Integrations

**Analysis Date:** 2026-01-19

## APIs & External Services

**SIEM Platforms (Inbound Webhooks):**
- Elastic SIEM - Alert ingestion via webhook
  - Endpoint: `POST /api/v1/webhooks/elastic`
  - Auth: HMAC-SHA256 signature verification (`X-Elastic-Signature` header)
  - Env vars: `ELASTIC_SIEM_URL`, `ELASTIC_SIEM_API_KEY`, `ELASTIC_SIEM_WEBHOOK_SECRET`
  - Implementation: `app/api/v1/webhooks.py`

- Azure Sentinel - Alert ingestion via webhook
  - Endpoint: `POST /api/v1/webhooks/sentinel`
  - Auth: None configured (add signature verification)
  - Env vars: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
  - Implementation: `app/api/v1/webhooks.py`

- Splunk - Alert ingestion via webhook
  - Endpoint: `POST /api/v1/webhooks/splunk`
  - Auth: None configured
  - Implementation: `app/api/v1/webhooks.py`

**Threat Intelligence:**
- MITRE ATT&CK Framework
  - Library: `mitreattack-python` >=5.3.0
  - Format: STIX 2.1 (`stix2` library)
  - Navigator layer export: `GET /api/v1/mitre/navigator/layer`
  - Implementation: `app/api/v1/mitre_attack.py`

- Generic Threat Intel Feed
  - Env var: `THREAT_INTEL_API_KEY`
  - Dark web monitoring toggle: `DARK_WEB_MONITORING_ENABLED`
  - Model: `app/models/threat_intel.py`

**Cloud Platform Integrations (Prepared, Not Fully Implemented):**
- Azure
  - Event Hub connection string: `AZURE_EVENT_HUB_CONNECTION_STRING`
  - Subscription: `AZURE_SUBSCRIPTION_ID`

- AWS
  - Region: `AWS_REGION` (default: us-east-1)
  - Kinesis stream: `AWS_KINESIS_STREAM_NAME`
  - Credentials: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

- GCP
  - Pub/Sub subscription: `GCP_PUBSUB_SUBSCRIPTION`
  - Credentials: `GCP_CREDENTIALS_PATH`

- OCI (Oracle Cloud)
  - Region: `OCI_REGION`
  - Auth: `OCI_TENANCY_OCID`, `OCI_USER_OCID`, `OCI_FINGERPRINT`, `OCI_KEY_FILE`

## Data Storage

**Databases:**
- PostgreSQL 16 with TimescaleDB
  - Connection: `DATABASE_URL` (format: `postgresql+asyncpg://user:pass@host:5432/db`)
  - Client: SQLAlchemy async with `asyncpg` driver
  - Pool size: 20 (configurable via `DATABASE_POOL_SIZE`)
  - Implementation: `app/db/base.py`

- Elasticsearch 8.15
  - Connection: `ELASTICSEARCH_URL` (default: http://localhost:9200)
  - Auth: `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD`
  - Index prefix: `ELASTICSEARCH_INDEX_PREFIX` (default: corerecon-soc)
  - Client: `elasticsearch[async]`

**Caching:**
- Redis 7
  - Connection: `REDIS_URL` (format: redis://:password@host:6379/0)
  - Uses: WebSocket pub/sub, real-time event distribution
  - Channels: `soc:alerts`, `soc:incidents`, `soc:dashboard`
  - Implementation: `app/websocket/manager.py`

**File Storage:**
- Local filesystem only (no cloud storage configured)
- Evidence attachments: Not yet implemented

## Authentication & Identity

**Auth Provider:**
- Custom JWT-based authentication
  - Implementation: `app/core/security.py`, `app/api/v1/auth.py`
  - Algorithm: HS256 (configurable via `JWT_ALGORITHM`)
  - Access token expiry: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
  - Refresh token expiry: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)

**Password Hashing:**
- bcrypt via `passlib`
- Implementation: `app/core/security.py`

**OAuth2:**
- OAuth2PasswordBearer flow
- Token URL: `/api/v1/auth/login`

## Monitoring & Observability

**Metrics:**
- Prometheus client (`prometheus-client` >=0.21.0)
- Metrics endpoint: Not yet exposed (library available)

**Logging:**
- structlog >=24.4.0 for structured JSON logging
- Log level: configurable via `LOG_LEVEL` (default: INFO)
- Log format: configurable via `LOG_FORMAT` (default: json)

**Error Tracking:**
- None configured (Sentry recommended for production)

## CI/CD & Deployment

**Hosting:**
- Docker containers
- Docker Compose orchestration (`docker-compose.yml`)
- Services: postgres, redis, elasticsearch, kibana, backend, frontend

**CI Pipeline:**
- GitHub Actions (`.github/workflows/security-pipeline.yml`)
- Jobs:
  - SAST: Bandit, Semgrep
  - CodeQL Analysis
  - Dependency Scan: pip-audit
  - Security Gate Check
- Scheduled: Weekly security scan (Sunday midnight)

## Environment Configuration

**Required env vars (critical for operation):**
- `DATABASE_URL` - PostgreSQL connection
- `SECRET_KEY` - JWT signing (change in production!)
- `ELASTICSEARCH_PASSWORD` - Elastic auth

**Optional env vars (for integrations):**
- `ELASTIC_SIEM_WEBHOOK_SECRET` - Webhook signature verification
- `REDIS_PASSWORD` - Redis authentication
- Cloud platform credentials (Azure, AWS, GCP, OCI)

**Secrets location:**
- Environment variables (no secrets management service configured)
- `.env` file for local development (gitignored)
- `.env.example` provides template with placeholder values

## Webhooks & Callbacks

**Incoming (Alert Ingestion):**
- `POST /api/v1/webhooks/elastic` - Elastic SIEM alerts
- `POST /api/v1/webhooks/sentinel` - Azure Sentinel alerts
- `POST /api/v1/webhooks/splunk` - Splunk alerts

**Outgoing:**
- None configured
- Email notifications prepared but not implemented:
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`

## Real-Time Communication

**WebSocket Endpoints:**
- `ws://{host}/ws/alerts` - Real-time alert streaming
- `ws://{host}/ws/incidents` - Incident updates
- `ws://{host}/ws/dashboard` - Dashboard metric updates

**Implementation:**
- `app/websocket/manager.py` - Connection manager with Redis pub/sub
- `app/websocket/handlers.py` - WebSocket route handlers

**Stats Endpoint:**
- `GET /ws/stats` - Connection statistics

## Visualization

**Kibana:**
- Version: 8.15.0
- Port: 5601
- Connected to Elasticsearch for log visualization

**MITRE ATT&CK Navigator:**
- Layer export: `GET /api/v1/mitre/navigator/layer`
- Format: Navigator Layer 4.5 JSON
- Domain: enterprise-attack

## Detection Rules

**Supported Formats:**
- Sigma rules
- YARA rules
- Custom rule format
- Implementation: `app/api/v1/detection_rules.py`, `app/models/detection_rule.py`

**Rule Management:**
- CRUD operations via `/api/v1/detection-rules/`
- Enable/disable rules
- Rule tuning history

---

*Integration audit: 2026-01-19*
