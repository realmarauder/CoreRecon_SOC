# Requirements - v1.1 Production Ready

**Created:** 2026-01-19
**Milestone:** v1.1 - Production Ready

---

## v1 Requirements (This Milestone)

### Security Hardening

- [ ] **SEC-01**: Implement webhook signature verification for Azure Sentinel
- [ ] **SEC-02**: Implement webhook signature verification for Splunk HEC
- [ ] **SEC-03**: Implement logout token invalidation via Redis blacklist
- [ ] **SEC-04**: Add rate limiting on `/auth/login` (5 attempts/min/IP)
- [ ] **SEC-05**: Add startup validation rejecting default credentials in production
- [ ] **SEC-06**: Restrict CORS to explicit methods and headers

### Test Infrastructure

- [ ] **TEST-01**: Create `tests/conftest.py` with database and client fixtures
- [ ] **TEST-02**: Implement authentication tests (login, token refresh, protected routes)
- [ ] **TEST-03**: Implement alert CRUD tests with pagination and filtering
- [ ] **TEST-04**: Implement incident CRUD tests with lifecycle transitions
- [ ] **TEST-05**: Implement webhook normalization tests (Elastic, Sentinel, Splunk)
- [ ] **TEST-06**: Implement correlation service tests
- [ ] **TEST-07**: Achieve 80%+ coverage on core modules

### Database Migrations

- [ ] **DB-01**: Create initial Alembic migration with all current tables
- [ ] **DB-02**: Add migration for `Alert.category` column
- [ ] **DB-03**: Add FK constraint on `Alert.escalated_to_incident_id`

### Frontend Application

- [ ] **FE-01**: Setup React + Vite + TypeScript + Material-UI project
- [ ] **FE-02**: Implement authentication flow (login, logout, token refresh)
- [ ] **FE-03**: Implement dashboard with KPI cards and alert trends
- [ ] **FE-04**: Implement alert list with filtering, sorting, pagination
- [ ] **FE-05**: Implement alert detail panel with observables and MITRE mapping
- [ ] **FE-06**: Implement bulk alert operations (acknowledge, assign, close)
- [ ] **FE-07**: Implement incident list and detail views
- [ ] **FE-08**: Implement incident timeline visualization
- [ ] **FE-09**: Implement MITRE ATT&CK coverage heatmap
- [ ] **FE-10**: Implement settings and user management pages
- [ ] **FE-11**: Implement WebSocket integration for real-time updates

### Functionality Polish

- [ ] **FUNC-01**: Implement geographic threat map with IP geolocation
- [ ] **FUNC-02**: Implement bulk alert operations API endpoint
- [ ] **FUNC-03**: Implement alert-to-incident escalation workflow
- [ ] **FUNC-04**: Optimize dashboard metrics query performance

---

## v2 Requirements (Deferred)

### Cloud Monitoring Connectors
- Azure Event Hubs consumer
- AWS Kinesis Firehose consumer
- GCP Pub/Sub subscriber
- OCI Streaming consumer

### Background Processing
- Celery/ARQ task queue setup
- Move enrichment to background tasks
- Move playbook execution to background tasks

### Playbook Automation
- Step execution engine
- Approval workflow
- External action integrations

### Advanced Features
- Dark web monitoring integration
- Threat feed aggregation
- Multi-tenant support

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| External Attack Surface Management | Tier 2 feature, not core SOC |
| Shadow IT identification | Requires network discovery |
| Breach probability modeling | ML complexity, defer to v3 |
| SOAR integration | Build internal automation first |
| Auto-remediation | Requires proven playbook engine |
| WCAG 2.2 AA accessibility | Address after frontend stable |
| On-premises syslog collector | Focus on cloud SIEM first |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 1 | Pending |
| SEC-02 | Phase 1 | Pending |
| SEC-03 | Phase 1 | Pending |
| SEC-04 | Phase 1 | Pending |
| SEC-05 | Phase 1 | Pending |
| SEC-06 | Phase 1 | Pending |
| DB-01 | Phase 2 | Pending |
| DB-02 | Phase 2 | Pending |
| DB-03 | Phase 2 | Pending |
| TEST-01 | Phase 3 | Pending |
| TEST-02 | Phase 3 | Pending |
| TEST-03 | Phase 3 | Pending |
| TEST-04 | Phase 3 | Pending |
| TEST-05 | Phase 3 | Pending |
| TEST-06 | Phase 3 | Pending |
| TEST-07 | Phase 3 | Pending |
| FUNC-01 | Phase 4 | Pending |
| FUNC-02 | Phase 4 | Pending |
| FUNC-03 | Phase 4 | Pending |
| FUNC-04 | Phase 4 | Pending |
| FE-01 | Phase 5 | Pending |
| FE-02 | Phase 5 | Pending |
| FE-03 | Phase 5 | Pending |
| FE-04 | Phase 6 | Pending |
| FE-05 | Phase 6 | Pending |
| FE-06 | Phase 6 | Pending |
| FE-07 | Phase 7 | Pending |
| FE-08 | Phase 7 | Pending |
| FE-09 | Phase 7 | Pending |
| FE-10 | Phase 8 | Pending |
| FE-11 | Phase 8 | Pending |

---

*Requirements defined: 2026-01-19*
