# Codebase Concerns

**Analysis Date:** 2026-01-19

## Tech Debt

**Non-Unique Ticket Number Generation:**
- Issue: `generate_ticket_number()` uses `random.randint()` which can produce duplicate ticket numbers
- Files: `app/api/v1/incidents.py` (lines 18-30)
- Impact: Race condition could create duplicate INC-YYYY-NNNNN ticket numbers under load
- Fix approach: Use database sequence, UUID, or atomic counter with Redis

**Duplicated IP/Hostname Extraction Logic:**
- Issue: Same extraction methods duplicated across AlertCorrelationService and AlertDeduplicationService
- Files: `app/services/correlation.py` (lines 102-130 and 255-283)
- Impact: Code maintenance burden; changes must be made in multiple places
- Fix approach: Extract to shared utility functions in a dedicated module

**Incomplete Logout Implementation:**
- Issue: `/logout` endpoint does nothing but `pass` - tokens remain valid
- Files: `app/api/v1/auth.py` (lines 260-275)
- Impact: Revoked user sessions remain valid until token expiry; security concern
- Fix approach: Implement token blacklist in Redis with TTL matching token expiry

**Missing `category` Field on Alert Model:**
- Issue: Correlation service references `alert1.category` but Alert model has no `category` column
- Files: `app/services/correlation.py` (line 96), `app/models/alert.py`
- Impact: Correlation by category always fails silently (returns 0)
- Fix approach: Add `category` column to Alert model and migration

**Placeholder Threat Map Endpoint:**
- Issue: `/dashboard/threats/map` returns hardcoded sample structure, no actual geolocation
- Files: `app/api/v1/dashboard.py` (lines 200-233)
- Impact: Feature advertised but not functional
- Fix approach: Integrate IP geolocation service (MaxMind GeoIP, ipstack, etc.)

## Known Bugs

**N+1 Query in Alert Trend Endpoint:**
- Symptoms: Slow response for `/dashboard/alerts/trend` with many time buckets
- Files: `app/api/v1/dashboard.py` (lines 151-197)
- Trigger: Request with small interval and large hour range (e.g., hours=168, interval=1)
- Workaround: Keep interval >= 4 hours for ranges > 24 hours
- Fix: Use single query with `date_trunc()` and `group by`

**Correlation Score Added as Dynamic Attribute:**
- Symptoms: `correlation_score` attribute disappears after ORM refresh
- Files: `app/services/correlation.py` (line 57)
- Trigger: Accessing `correlation_score` after any db operation
- Fix: Return tuple of (alert, score) or use separate response model

## Security Considerations

**Default Credentials in Config:**
- Risk: Production deployments may use default `changeme` passwords
- Files: `app/config.py` (lines 33-34, 49, 56-58), `.env.example`
- Current mitigation: `.env.example` documents required changes
- Recommendations:
  - Add startup validation that rejects default SECRET_KEY
  - Fail fast if `ENV=production` and secrets contain "changeme"

**Webhook Signature Verification Bypass:**
- Risk: Missing webhook secrets allow unverified requests
- Files: `app/api/v1/webhooks.py` (lines 35-37)
- Current mitigation: Logs warning but processes request anyway
- Recommendations:
  - Make webhook secret required in production
  - Return 403 if signature verification is bypassed

**Azure Sentinel Webhook Has No Signature Verification:**
- Risk: Anyone can submit fake Sentinel alerts
- Files: `app/api/v1/webhooks.py` (lines 214-253)
- Current mitigation: None
- Recommendations: Implement Azure Event Hub signature validation or require API key

**Splunk Webhook Has No Signature Verification:**
- Risk: Anyone can submit fake Splunk alerts
- Files: `app/api/v1/webhooks.py` (lines 286-358)
- Current mitigation: None
- Recommendations: Add Splunk HEC token validation

**No Rate Limiting on Auth Endpoints:**
- Risk: Brute force attacks on `/api/v1/auth/login`
- Files: `app/api/v1/auth.py`
- Current mitigation: None
- Recommendations: Add slowapi rate limiter or nginx rate limiting

**CORS Allows All Methods and Headers:**
- Risk: Overly permissive CORS policy
- Files: `app/main.py` (lines 42-48)
- Current mitigation: Origins are restricted
- Recommendations: Specify explicit allowed methods and headers

## Performance Bottlenecks

**Dashboard Metrics Makes 9 Separate Queries:**
- Problem: Each metric fetches separately instead of batching
- Files: `app/api/v1/dashboard.py` (lines 17-148)
- Cause: Sequential individual count/avg queries
- Improvement path: Combine into single query with multiple aggregates or use Redis caching

**Deduplication Scans All Recent Alerts:**
- Problem: `find_duplicate()` loads all alerts in time window, calculates hash for each
- Files: `app/services/correlation.py` (lines 191-227)
- Cause: No database index on hash, computes hash in Python
- Improvement path: Store dedup hash in Alert model, add index, query by hash directly

**Alert Correlation Has No Index Optimization:**
- Problem: Correlation query only filters by time, then scores all candidates in Python
- Files: `app/services/correlation.py` (lines 19-63)
- Cause: Multi-factor scoring not database-optimized
- Improvement path: Add indexes on source_ip, hostname; pre-filter on key fields

## Fragile Areas

**WebSocket Manager Global State:**
- Files: `app/websocket/manager.py`
- Why fragile: Single global instance; Redis reconnection not gracefully handled
- Safe modification: Add Redis connection health checks and auto-reconnect
- Test coverage: No tests for WebSocket functionality

**Database Session Auto-Commit Pattern:**
- Files: `app/db/base.py` (lines 47-55)
- Why fragile: `get_db()` commits on success even if caller expects read-only; exception swallowed on rollback
- Safe modification: Explicit commit in route handlers; remove auto-commit
- Test coverage: No database tests exist

**SLA Calculation Tied to Incident Creation:**
- Files: `app/api/v1/incidents.py` (lines 33-57)
- Why fragile: SLA times only set at creation; changing severity via update doesn't recalculate (fixed in escalate)
- Safe modification: Recalculate SLA on any severity change, not just escalation
- Test coverage: None

## Scaling Limits

**In-Memory WebSocket Connection Tracking:**
- Current capacity: Limited by single instance memory
- Limit: Cannot scale horizontally without losing connection tracking
- Scaling path: Redis-backed connection registry per instance + pub/sub already partially implemented

**PostgreSQL Connection Pool:**
- Current capacity: 20 connections + 10 overflow = 30 max
- Limit: Heavy concurrent load may exhaust pool
- Scaling path: Consider PgBouncer; increase pool for production; add connection pool metrics

**Elasticsearch Single Node:**
- Current capacity: One node in docker-compose
- Limit: No high availability; data loss on node failure
- Scaling path: Multi-node cluster with replicas in production

## Dependencies at Risk

**`aioredis` Deprecated:**
- Risk: Package deprecated; merged into `redis-py`
- Impact: Future incompatibility, no security updates
- Migration plan: Replace with `redis[async]` (already included in requirements.txt)
- Files: `requirements.txt` (line 10)

**`sqlalchemy.ext.declarative` Deprecation Warning:**
- Risk: SQLAlchemy 2.0 recommends `sqlalchemy.orm.declarative_base`
- Impact: Future SQLAlchemy versions may remove old import
- Migration plan: Update import in `app/db/base.py` (line 5)

## Missing Critical Features

**No Test Suite:**
- Problem: Zero test files found despite pytest in requirements.txt
- Blocks: Safe refactoring; confident deployments; CI/CD
- Files: `requirements.txt` includes testing deps but no `tests/` directory exists

**No Database Migrations for Initial Schema:**
- Problem: Alembic configured but no migration files visible
- Blocks: Reproducible database setup
- Files: `alembic/` directory exists but empty env.py

**No Playbook Step Execution Engine:**
- Problem: Playbook execution creates records but no actual automation runs
- Blocks: Automated incident response
- Files: `app/api/v1/playbooks.py` - only tracking, no execution

**No Incident/Alert Relationship:**
- Problem: No foreign key or escalation link between Alert and Incident models
- Blocks: Alert-to-incident escalation workflow; incident context from source alerts
- Files: `app/models/alert.py` (line 51 has `escalated_to_incident_id` but no FK constraint)

**No Background Task Processing:**
- Problem: No Celery, ARQ, or background worker for async operations
- Blocks: Long-running tasks (enrichment, playbook execution, bulk operations)
- Current workaround: Redis pub/sub for WebSocket only

## Test Coverage Gaps

**All Modules Untested:**
- What's not tested: Entire codebase - no test files exist
- Files: All files under `app/`
- Risk: Any change could introduce regressions undetected
- Priority: High

**Critical Untested Paths:**
- Authentication flow (`app/api/v1/auth.py`)
- Alert/Incident CRUD operations
- Webhook payload normalization
- Correlation and deduplication logic
- SLA breach detection
- Priority: High - these are core business logic

---

*Concerns audit: 2026-01-19*
