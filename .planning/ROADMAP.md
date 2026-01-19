# Roadmap - v1.1 Production Ready

**Created:** 2026-01-19
**Milestone:** v1.1 - Production Ready

---

## Overview

| Phase | Name | Requirements | Status |
|-------|------|--------------|--------|
| 1 | Security Hardening | SEC-01 to SEC-06 | Planned |
| 2 | Database Migrations | DB-01 to DB-03 | Not Started |
| 3 | Test Infrastructure | TEST-01 to TEST-07 | Not Started |
| 4 | Functionality Polish | FUNC-01 to FUNC-04 | Not Started |
| 5 | Frontend Foundation | FE-01 to FE-03 | Not Started |
| 6 | Frontend Alerts | FE-04 to FE-06 | Not Started |
| 7 | Frontend Incidents | FE-07 to FE-09 | Not Started |
| 8 | Frontend Polish | FE-10 to FE-11 | Not Started |

---

## Phase 1: Security Hardening

**Goal:** Close all P1 security gaps before any production deployment.

**Plans:** 3 plans in 2 waves

| Wave | Plans | Description |
|------|-------|-------------|
| 1 | 01-01 | Startup validation + CORS restriction |
| 2 | 01-02, 01-03 | Token blacklist + rate limiting, Webhook auth (parallel) |

Plans:
- [ ] 01-01-PLAN.md - Startup validation and CORS restriction (SEC-05, SEC-06)
- [ ] 01-02-PLAN.md - Token blacklist and rate limiting (SEC-03, SEC-04)
- [ ] 01-03-PLAN.md - Webhook signature verification (SEC-01, SEC-02)

**Requirements:**
- SEC-01: Webhook signature verification for Azure Sentinel
- SEC-02: Webhook signature verification for Splunk HEC
- SEC-03: Logout token invalidation via Redis blacklist
- SEC-04: Rate limiting on `/auth/login`
- SEC-05: Startup validation rejecting default credentials
- SEC-06: Restrict CORS configuration

**Success Criteria:**
1. Sentinel webhook rejects requests without valid signature
2. Splunk webhook validates HEC token
3. Logged-out tokens cannot access protected routes
4. Brute force login attempts are blocked after 5 failures
5. Application fails to start if `changeme` secrets detected in production

**Dependencies:** None

---

## Phase 2: Database Migrations

**Goal:** Make database schema reproducible and add missing columns.

**Requirements:**
- DB-01: Initial Alembic migration with all current tables
- DB-02: Migration for `Alert.category` column
- DB-03: FK constraint on `Alert.escalated_to_incident_id`

**Success Criteria:**
1. `alembic upgrade head` creates complete schema on empty database
2. `Alert.category` column exists and accepts values
3. Alert-to-incident relationship enforced by database
4. `alembic downgrade` works without errors

**Dependencies:** None

---

## Phase 3: Test Infrastructure

**Goal:** Establish comprehensive test coverage on critical paths.

**Requirements:**
- TEST-01: `tests/conftest.py` with fixtures
- TEST-02: Authentication tests
- TEST-03: Alert CRUD tests
- TEST-04: Incident CRUD tests
- TEST-05: Webhook normalization tests
- TEST-06: Correlation service tests
- TEST-07: 80%+ coverage on core modules

**Success Criteria:**
1. `pytest tests/ -v` runs without errors
2. All auth flows tested (login, refresh, logout, protected)
3. All CRUD operations tested for alerts and incidents
4. Webhook payloads from all 3 SIEMs normalize correctly
5. Coverage report shows 80%+ on `app/core/` and `app/api/`

**Dependencies:** Phase 2 (migrations needed for test database)

---

## Phase 4: Functionality Polish

**Goal:** Complete backend functionality gaps before frontend work.

**Requirements:**
- FUNC-01: Geographic threat map with IP geolocation
- FUNC-02: Bulk alert operations API endpoint
- FUNC-03: Alert-to-incident escalation workflow
- FUNC-04: Dashboard metrics query optimization

**Success Criteria:**
1. `/dashboard/threats/map` returns real geolocated threat data
2. `POST /api/v1/alerts/bulk` accepts batch operations
3. `POST /api/v1/alerts/{id}/escalate` creates linked incident
4. Dashboard metrics load in < 500ms (single optimized query)

**Dependencies:** Phase 2 (Alert.category needed), Phase 3 (tests for new endpoints)

---

## Phase 5: Frontend Foundation

**Goal:** Establish React application with auth and dashboard.

**Requirements:**
- FE-01: React + Vite + TypeScript + Material-UI setup
- FE-02: Authentication flow (login, logout, refresh)
- FE-03: Dashboard with KPI cards and trends

**Success Criteria:**
1. `npm run dev` starts frontend on port 3000
2. Login form authenticates against API
3. Dashboard displays 5 KPI cards with real data
4. Alert trend chart shows last 24 hours
5. Protected routes redirect to login when unauthenticated

**Dependencies:** Phase 1-4 (backend must be secure and functional)

---

## Phase 6: Frontend Alerts

**Goal:** Complete alert management UI.

**Requirements:**
- FE-04: Alert list with filtering, sorting, pagination
- FE-05: Alert detail panel with observables and MITRE
- FE-06: Bulk alert operations UI

**Success Criteria:**
1. Alert list supports severity/status/source filters
2. Clicking alert opens detail drawer
3. MITRE ATT&CK techniques displayed with links
4. Checkbox selection enables bulk action buttons
5. Bulk acknowledge/assign/close work correctly

**Dependencies:** Phase 5 (foundation), FUNC-02 (bulk API)

---

## Phase 7: Frontend Incidents

**Goal:** Complete incident management UI.

**Requirements:**
- FE-07: Incident list and detail views
- FE-08: Incident timeline visualization
- FE-09: MITRE ATT&CK coverage heatmap

**Success Criteria:**
1. Incident list shows open cases with SLA indicators
2. Incident detail shows full case information
3. Timeline shows chronological audit trail
4. ATT&CK heatmap highlights covered techniques
5. Navigator JSON export works

**Dependencies:** Phase 6 (alert UI patterns)

---

## Phase 8: Frontend Polish

**Goal:** Complete remaining UI and real-time integration.

**Requirements:**
- FE-10: Settings and user management pages
- FE-11: WebSocket integration for real-time updates

**Success Criteria:**
1. Settings page allows profile updates
2. User management (admin only) shows user list
3. New alerts appear in list without refresh
4. Incident updates reflect in real-time
5. Connection status indicator shows WebSocket state

**Dependencies:** Phase 7 (all core views complete)

---

## Progress Tracking

| Phase | Started | Completed | Notes |
|-------|---------|-----------|-------|
| 1 | - | - | 3 plans in 2 waves |
| 2 | - | - | |
| 3 | - | - | |
| 4 | - | - | |
| 5 | - | - | |
| 6 | - | - | |
| 7 | - | - | |
| 8 | - | - | |

---

*Roadmap created: 2026-01-19*
*Phase 1 planned: 2026-01-19*
