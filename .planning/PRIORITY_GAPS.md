# CoreRecon SOC - Prioritized Gap Closure Plan

**Created:** 2026-01-19

---

## Priority Matrix

Gaps ranked by: **Impact on John's SOC Operations** × **Security Risk** × **Effort**

---

## 🔴 P0: Blockers (Must Fix Before Any Use)

These prevent John from using the system at all.

### 1. Frontend Application
- **Gap:** No React + Material-UI frontend exists
- **Impact:** John cannot interact with the SOC - there's no UI
- **Effort:** 2-3 weeks
- **Dependencies:** None (API is ready)
- **Deliverables:**
  - Dashboard with KPI cards, alert trends, threat map
  - Alert list with filtering, bulk actions, detail panel
  - Incident management with timeline, observables, evidence
  - MITRE ATT&CK coverage heatmap
  - Settings and user management

### 2. Test Suite Foundation
- **Gap:** Zero test files despite pytest in requirements
- **Impact:** Cannot safely deploy or modify code
- **Effort:** 3-5 days
- **Dependencies:** None
- **Deliverables:**
  - `tests/conftest.py` with fixtures
  - Auth tests (login, token refresh, protected routes)
  - Alert CRUD tests
  - Incident CRUD tests
  - Webhook normalization tests

### 3. Database Migrations
- **Gap:** Alembic configured but no migration files
- **Impact:** Cannot reproduce database schema reliably
- **Effort:** 1 day
- **Dependencies:** None
- **Deliverables:**
  - Initial migration with all current tables
  - Migration for any missing columns (Alert.category)

---

## 🟠 P1: Security Critical (Fix Before Production)

These are security vulnerabilities that must be addressed.

### 4. Webhook Signature Verification
- **Gap:** Sentinel and Splunk webhooks accept unsigned requests
- **Impact:** Anyone can inject fake alerts
- **Effort:** 2-3 hours each
- **Deliverables:**
  - Azure Sentinel: Event Hub signature validation or API key
  - Splunk: HEC token validation

### 5. Logout Token Invalidation
- **Gap:** `/logout` does nothing - tokens remain valid
- **Impact:** Revoked sessions stay active until expiry
- **Effort:** 4-6 hours
- **Deliverables:**
  - Redis token blacklist with TTL
  - Check blacklist on every protected request

### 6. Rate Limiting on Auth
- **Gap:** No protection against brute force on `/auth/login`
- **Impact:** Password guessing attacks possible
- **Effort:** 2-3 hours
- **Deliverables:**
  - slowapi rate limiter or nginx config
  - 5 attempts per minute per IP

### 7. Default Credential Rejection
- **Gap:** "changeme" passwords accepted in production
- **Impact:** Insecure deployments
- **Effort:** 1-2 hours
- **Deliverables:**
  - Startup validation that rejects default SECRET_KEY
  - Fail fast if ENV=production and secrets contain "changeme"

---

## 🟡 P2: Functionality Gaps (Required for SOC Operations)

These affect John's ability to run effective SOC operations.

### 8. Geographic Threat Map
- **Gap:** Returns hardcoded placeholder data
- **Impact:** No geographic visibility into threats
- **Effort:** 1 day
- **Deliverables:**
  - MaxMind GeoIP or ipstack integration
  - Real IP geolocation for alerts

### 9. Bulk Alert Operations
- **Gap:** Only individual alert operations
- **Impact:** Slow triage when handling many alerts
- **Effort:** 4-6 hours
- **Deliverables:**
  - `POST /api/v1/alerts/bulk` endpoint
  - Actions: acknowledge, assign, close, suppress

### 10. Alert-to-Incident Escalation
- **Gap:** No proper FK link or escalation workflow
- **Impact:** Losing context from source alerts
- **Effort:** 1 day
- **Deliverables:**
  - Add FK constraint to `escalated_to_incident_id`
  - `POST /api/v1/alerts/{id}/escalate` endpoint
  - Copy alert data to incident

### 11. Missing Alert.category Field
- **Gap:** Correlation service references non-existent field
- **Impact:** Category-based correlation always fails
- **Effort:** 2-3 hours
- **Deliverables:**
  - Add `category` column to Alert model
  - Migration for new column

---

## 🟢 P3: Enhancement Gaps (Improve SOC Effectiveness)

These improve the system but aren't blockers.

### 12. Cloud Monitoring Connectors
- **Gap:** Config exists but no actual streaming services
- **Impact:** Cannot monitor client cloud environments
- **Effort:** 1 week per cloud (4 weeks total)
- **Deliverables:**
  - Azure: Event Hubs consumer
  - AWS: Kinesis Firehose consumer
  - GCP: Pub/Sub subscriber
  - OCI: Streaming consumer

### 13. Background Task Processing
- **Gap:** No Celery/ARQ for async operations
- **Impact:** Long-running tasks block API
- **Effort:** 2-3 days
- **Deliverables:**
  - ARQ or Celery setup
  - Move enrichment, playbook execution to background

### 14. Playbook Execution Engine
- **Gap:** Records created but no automation runs
- **Impact:** Manual incident response only
- **Effort:** 1-2 weeks
- **Deliverables:**
  - Step execution engine
  - Approval workflow
  - External action integrations

### 15. Dashboard Performance
- **Gap:** 9 separate queries for metrics
- **Impact:** Slow dashboard load
- **Effort:** 4-6 hours
- **Deliverables:**
  - Combined query with multiple aggregates
  - Redis caching for metrics

---

## Recommended Implementation Order

```
Week 1-2: Foundation
├── [P0] Database migrations (1 day)
├── [P0] Test suite foundation (5 days)
├── [P1] Webhook signature verification (1 day)
├── [P1] Logout token invalidation (1 day)
├── [P1] Rate limiting (0.5 day)
├── [P1] Default credential rejection (0.5 day)
└── [P2] Missing Alert.category field (0.5 day)

Week 3-5: Frontend
└── [P0] React + MUI frontend (2-3 weeks)
    ├── Dashboard
    ├── Alerts
    ├── Incidents
    ├── Threat Intel
    └── Settings

Week 6: Functionality
├── [P2] Geographic threat map (1 day)
├── [P2] Bulk alert operations (1 day)
├── [P2] Alert-to-incident escalation (1 day)
└── [P3] Dashboard performance (1 day)

Week 7-8: Advanced
├── [P3] Background task processing (3 days)
└── [P3] Playbook execution engine (7 days)

Week 9-12: Cloud Monitoring
└── [P3] Cloud connectors (4 weeks)
    ├── Azure Event Hubs
    ├── AWS Kinesis
    ├── GCP Pub/Sub
    └── OCI Streaming
```

---

## Quick Wins (< 1 day each)

1. ✅ Missing Alert.category field (2-3 hours)
2. ✅ Default credential rejection (1-2 hours)
3. ✅ Rate limiting (2-3 hours)
4. ✅ Database migrations (1 day)
5. ✅ Webhook signature verification (1 day)

**Total quick wins: ~3 days → significantly improved security posture**

---

## Milestone Suggestion

For `/gsd:new-milestone`, I recommend:

**Milestone: "v1.1 - Production Ready"**

**Goal:** Close all P0 and P1 gaps, deliver functional frontend

**Phases:**
1. Security Hardening (P1 items)
2. Test Infrastructure (P0)
3. Frontend MVP (P0)
4. Functionality Polish (P2 critical items)

**Success Criteria:**
- John can log in and see the dashboard
- All SIEM webhooks have signature verification
- 80%+ test coverage on critical paths
- Database schema is reproducible via migrations

---

*Priority analysis: 2026-01-19*
