# CoreRecon SOC

**Created:** 2026-01-19
**Last Updated:** 2026-01-19

---

## Core Value

**The ONE thing that must work:** Real-time security alert monitoring and incident management for John's MSP clients, enabling effective SOC operations from a single pane of glass.

---

## Vision

CoreRecon SOC is a multi-tenant Security Operations Center platform for John's MSP practice. It aggregates security alerts from multiple SIEMs (Elastic, Azure Sentinel, Splunk), provides incident management with SLA tracking, and offers threat intelligence correlation using the MITRE ATT&CK framework.

**Target Users:**
- SOC analysts triaging alerts
- Incident responders managing cases
- Security managers viewing KPIs

**Key Differentiators:**
- Multi-cloud monitoring (Azure, AWS, GCP, OCI)
- MITRE ATT&CK heatmap visualization
- Real-time WebSocket updates
- Self-hosted on-premises deployment

---

## Active Requirements

### v1.0 Foundation (Shipped)

The following core capabilities have been implemented:

**Alert Management:**
- [x] Real-time WebSocket delivery (sub-2-second)
- [x] Severity classification (Critical/High/Medium/Low/Info)
- [x] Alert deduplication with configurable windows
- [x] SIEM webhook ingestion (Elastic, Sentinel, Splunk)

**Incident Management:**
- [x] 8-state lifecycle workflow
- [x] SLA timers with auto-escalation
- [x] Observable/IOC tracking with TLP classification
- [x] Incident timeline audit trail

**Threat Intelligence:**
- [x] IOC management (IP, domain, URL, hash, email)
- [x] Threat actor profiling with MITRE ATT&CK mapping
- [x] Detection rule management (Sigma, YARA, custom)

**Infrastructure:**
- [x] FastAPI async REST API
- [x] PostgreSQL + TimescaleDB
- [x] Redis pub/sub for real-time updates
- [x] Elasticsearch event store
- [x] Docker deployment ready

---

## Validated Requirements

These have been built and work correctly:

- JWT authentication with refresh tokens
- Role-based access control (admin, analyst, viewer)
- Alert correlation service
- Alert deduplication service
- MITRE ATT&CK Navigator export
- WebSocket connection management
- Elastic SIEM webhook with signature verification

---

## Current Milestone: v1.1 - Production Ready

**Goal:** Close all P0 and P1 gaps to make the system deployable and usable.

**Target features:**
- React + Material-UI frontend (P0 blocker)
- Comprehensive test suite (P0 blocker)
- Database migrations (P0 blocker)
- Security hardening (P1 critical)
- Functionality polish (P2 required)

---

## Constraints

- **Self-hosted:** Must run entirely on-premises, no cloud dependencies
- **Single developer:** John builds and maintains this
- **MSP use case:** Multi-tenant eventually, single-tenant for v1.x
- **Technology locked:** FastAPI, PostgreSQL, Redis, React + MUI

---

## Out of Scope (v1.x)

- Multi-tenancy
- External Attack Surface Management
- Shadow IT identification
- Breach probability modeling
- SOAR integration
- Auto-remediation workflows

---

*Project initialized: 2026-01-19*
