# Unified Security Operations Center (SOC) Application Requirements Document

**Version 1.0 | January 2026 | For Claude Code Development**

This comprehensive requirements document provides everything needed to build a production-ready SOC application with real-time bi-directional communication, multi-cloud monitoring, Elastic SIEM integration, and Google Workspace-style aesthetics. The specifications are derived from competitor analysis of Detect Solutions, Cyfax.ai, SOCRadar, and NTT Data, combined with industry best practices.

---

## Executive summary and key requirements

Building a unified SOC platform requires combining **threat intelligence aggregation**, **real-time alerting**, **incident management**, and **compliance reporting** into a single-pane-of-glass interface. Based on competitor analysis, the most successful platforms share these critical capabilities: sub-2-second alert delivery, MITRE ATT&CK framework mapping, multi-tenant architecture, and API-first design for SIEM/SOAR integrations.

**Core Value Proposition**: Deliver enterprise-grade SOC capabilities through a pip-installable Python application with configurable ports, Material Design 3 aesthetics, and comprehensive multi-cloud visibility.

**Primary Target Users**: SOC analysts (Tier 1-3), threat hunters, incident responders, and security managers requiring 24/7 monitoring capabilities.

---

## Technology stack specifications

### Backend framework: FastAPI

**Justification**: FastAPI delivers **2,847 requests/second** for REST endpoints (vs Django's 1,205) and handles **3,200+ concurrent WebSocket connections** per instance. Its async-first design is essential for real-time SOC dashboards processing thousands of alerts.

```python
# requirements.txt - Core Dependencies
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
websockets>=13.0
sqlalchemy[asyncio]>=2.0.36
asyncpg>=0.30.0
alembic>=1.14.0
redis>=5.2.0
hiredis>=3.0.0
elasticsearch[async]>=8.17.0
httpx>=0.28.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
orjson>=3.10.0
python-dotenv>=1.0.0
mitreattack-python>=5.3.0
```

### Database architecture

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Primary** | PostgreSQL + Async SQLAlchemy | Users, incidents, rules, configurations |
| **Time-Series** | TimescaleDB extension | Security metrics, 20x faster aggregations |
| **Event Store** | Elasticsearch 8.x | Log search, SIEM integration, ML anomaly detection |
| **Cache/PubSub** | Redis | Real-time WebSocket distribution, session caching |

### Frontend framework: React + Material-UI

React 18+ with MUI v5 implements Material Design 3 for Google Workspace-style aesthetics. Key packages: `@mui/material`, `@mui/icons-material`, `@mui/x-data-grid` for alert tables.

---

## Feature specifications from competitor analysis

### Tier 1 features (must-have based on competitor analysis)

**Alert Management**:
- Real-time alert ingestion via WebSocket with **sub-2-second delivery** (Detect Solutions benchmark)
- Multi-source alert aggregation from SIEM, EDR, cloud platforms
- Alert severity classification: Critical, High, Medium, Low, Informational
- Alert deduplication and correlation with configurable time windows
- Bulk actions: assign, acknowledge, suppress, close, escalate

**Incident Management**:
- Incident lifecycle tracking: New → Assigned → Investigating → Contained → Eradicated → Recovered → Closed
- SLA timers with automatic escalation (Critical: 15 min first response)
- Observable/IOC tracking with TLP classification (WHITE/GREEN/AMBER/RED)
- Evidence chain of custody with cryptographic hashing
- Playbook attachment and execution status tracking

**Threat Intelligence**:
- IOC management (IP, domain, URL, hash, email) with automatic rechecking
- Dark web monitoring integration (SOCRadar pattern: 20,000+ source coverage)
- Threat actor profiling with MITRE ATT&CK TTP mapping
- Threat feed aggregation from **30+ premium sources** (Cyfax benchmark)

**Dashboard & Visualization**:
- Executive KPI dashboard with real-time metrics
- Alert trend visualization (line charts, sparklines)
- Geographic threat map with WebGL rendering
- MITRE ATT&CK coverage heatmap
- Multi-tenant views for MSP deployments

### Tier 2 features (competitive differentiation)

**External Attack Surface Management**:
- Asset discovery from domain-only input (SOCRadar pattern)
- Shadow IT identification
- SSL certificate and domain expiration monitoring
- Vulnerability correlation with threat actor TTPs

**Predictive Intelligence**:
- Breach probability modeling (Detect Solutions: 7.2-week advance warning)
- Threat actor intent signal analysis
- Pre-breach telemetry correlation

**Automated Response**:
- Takedown request automation for phishing infrastructure
- SOAR integration via webhooks
- Auto-remediation workflows for common threats

---

## System architecture diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SOC Application Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Frontend (React + MUI)                            │   │
│  │   Dashboard │ Alerts │ Incidents │ Threat Intel │ Reports │ Settings │   │
│  └───────────────────────────┬─────────────────────────────────────────┘   │
│                              │ REST API + WebSocket (wss://)                │
│  ┌───────────────────────────▼─────────────────────────────────────────┐   │
│  │                    FastAPI Application Server                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ REST API    │  │ WebSocket   │  │ Background  │  │ Auth/RBAC  │ │   │
│  │  │ Endpoints   │  │ Manager     │  │ Workers     │  │ Module     │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └───────────────────────────┬─────────────────────────────────────────┘   │
│                              │                                              │
│  ┌───────────────────────────▼─────────────────────────────────────────┐   │
│  │                     Redis Pub/Sub Layer                              │   │
│  │            Real-time Alert Distribution + Session Cache              │   │
│  └───────────────────────────┬─────────────────────────────────────────┘   │
│                              │                                              │
│  ┌───────────┬───────────────┼───────────────┬─────────────────────────┐   │
│  │           │               │               │                         │   │
│  ▼           ▼               ▼               ▼                         │   │
│ PostgreSQL  TimescaleDB  Elasticsearch    Elastic SIEM               │   │
│ (Core Data) (Metrics)    (Event Store)   (Detection Engine)          │   │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                         External Integrations                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  Azure  │ │   AWS   │ │   GCP   │ │   OCI   │ │ On-Prem │           │
│  │ Monitor │ │CloudWatch│ │Chronicle│ │Streaming│ │ Syslog  │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Database schema specifications

### Core incident management tables

```sql
-- Incidents Table
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical','high','medium','low','informational')),
    status VARCHAR(30) NOT NULL DEFAULT 'new' CHECK (status IN ('new','assigned','investigating','contained','eradicated','recovered','closed','reopened')),
    category VARCHAR(50),
    detection_source VARCHAR(100),
    source_alert_id VARCHAR(255),
    source_system VARCHAR(50),
    assigned_analyst_id INTEGER REFERENCES users(id),
    assigned_team_id INTEGER REFERENCES teams(id),
    business_impact VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    first_response_at TIMESTAMP WITH TIME ZONE,
    containment_at TIMESTAMP WITH TIME ZONE,
    resolution_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    sla_breach BOOLEAN DEFAULT FALSE,
    playbook_id INTEGER REFERENCES playbooks(id),
    created_by INTEGER REFERENCES users(id)
);

-- Observables/IOCs Table
CREATE TABLE observables (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL CHECK (type IN ('ip','domain','url','hash_md5','hash_sha1','hash_sha256','email','filename','registry_key','user_account','process')),
    value TEXT NOT NULL,
    tlp VARCHAR(10) DEFAULT 'amber' CHECK (tlp IN ('white','green','amber','red')),
    is_malicious BOOLEAN,
    source VARCHAR(100),
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Affected Assets Table
CREATE TABLE affected_assets (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    asset_type VARCHAR(30) CHECK (asset_type IN ('host','server','network_device','application','database','user_account','cloud_resource')),
    identifier VARCHAR(255) NOT NULL,
    hostname VARCHAR(255),
    ip_address INET,
    criticality VARCHAR(20),
    owner VARCHAR(100),
    department VARCHAR(100),
    containment_status VARCHAR(30)
);

-- Incident Timeline/Audit Log
CREATE TABLE incident_timeline (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    actor_id INTEGER REFERENCES users(id),
    actor_type VARCHAR(20) CHECK (actor_type IN ('user','system','automation')),
    old_value JSONB,
    new_value JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- MITRE ATT&CK Mapping
CREATE TABLE incident_mitre_mapping (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    tactic VARCHAR(50),
    technique_id VARCHAR(20),
    technique_name VARCHAR(255),
    confidence VARCHAR(20) CHECK (confidence IN ('confirmed','likely','possible'))
);

-- Evidence with Chain of Custody
CREATE TABLE evidence (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_path VARCHAR(500),
    file_hash_sha256 VARCHAR(64),
    file_size BIGINT,
    mime_type VARCHAR(100),
    description TEXT,
    collected_by INTEGER REFERENCES users(id),
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    chain_of_custody JSONB
);

-- Detection Rules Table
CREATE TABLE detection_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_content TEXT,
    siem_platform VARCHAR(50),
    severity VARCHAR(20),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    modified_at TIMESTAMP
);

-- Rule-Technique Coverage Mapping
CREATE TABLE rule_technique_mapping (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES detection_rules(id),
    technique_id VARCHAR(20),
    coverage_score INTEGER CHECK (coverage_score BETWEEN 0 AND 100),
    confidence VARCHAR(20)
);

-- Performance Indexes
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_created_at ON incidents(created_at);
CREATE INDEX idx_observables_type_value ON observables(type, value);
CREATE INDEX idx_timeline_incident ON incident_timeline(incident_id, created_at);
```

### MITRE ATT&CK framework tables

```sql
-- Techniques Table
CREATE TABLE techniques (
    id SERIAL PRIMARY KEY,
    attack_id VARCHAR(20) UNIQUE NOT NULL,
    stix_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    detection TEXT,
    platforms JSONB,
    permissions_required JSONB,
    data_sources JSONB,
    is_subtechnique BOOLEAN DEFAULT FALSE,
    parent_technique_id VARCHAR(20),
    version VARCHAR(10),
    deprecated BOOLEAN DEFAULT FALSE
);

-- Tactics Table
CREATE TABLE tactics (
    id SERIAL PRIMARY KEY,
    attack_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    shortname VARCHAR(50),
    description TEXT,
    matrix_order INTEGER
);

-- Threat Groups Table
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    attack_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    aliases JSONB,
    description TEXT,
    country_origin VARCHAR(100),
    motivations JSONB,
    targeted_sectors JSONB
);

-- Coverage Analysis Table
CREATE TABLE coverage_analysis (
    id SERIAL PRIMARY KEY,
    technique_id INTEGER REFERENCES techniques(id),
    visibility_score INTEGER CHECK (visibility_score BETWEEN 0 AND 4),
    detection_score INTEGER CHECK (detection_score BETWEEN -1 AND 5),
    applicable_to VARCHAR(100),
    last_assessed TIMESTAMP,
    assessor VARCHAR(100),
    notes TEXT
);
```

---

## API endpoint specifications

### Core REST API endpoints

```yaml
# Base URL: /api/v1

# Authentication
POST   /auth/login                    # User authentication, returns JWT
POST   /auth/refresh                  # Refresh access token
POST   /auth/logout                   # Invalidate session

# Alert Management
GET    /alerts                        # List alerts with pagination/filtering
GET    /alerts/{id}                   # Get alert details
PATCH  /alerts/{id}                   # Update alert (status, assignment)
POST   /alerts/{id}/acknowledge       # Acknowledge alert
POST   /alerts/{id}/escalate          # Escalate to incident
POST   /alerts/bulk                   # Bulk operations

# Incident Management
GET    /incidents                     # List incidents
POST   /incidents                     # Create incident
GET    /incidents/{id}                # Get incident details
PATCH  /incidents/{id}                # Update incident
POST   /incidents/{id}/assign         # Assign to analyst
POST   /incidents/{id}/escalate       # Escalate to next tier
GET    /incidents/{id}/timeline       # Get incident audit trail
POST   /incidents/{id}/observables    # Add observable/IOC
POST   /incidents/{id}/evidence       # Upload evidence

# Threat Intelligence
GET    /threat-intel/iocs             # List IOCs
POST   /threat-intel/iocs             # Add IOC
GET    /threat-intel/actors           # List threat actors
GET    /threat-intel/feeds            # List threat feeds

# MITRE ATT&CK
GET    /attack/techniques             # List techniques
GET    /attack/techniques/{id}        # Get technique details
GET    /attack/coverage               # Get coverage statistics
GET    /attack/coverage/heatmap       # Get heatmap data
POST   /attack/navigator/layer        # Generate Navigator layer

# Dashboard
GET    /dashboard/metrics             # Get KPI metrics
GET    /dashboard/alerts/trend        # Get alert trend data
GET    /dashboard/threats/map         # Get geographic threat data

# Webhooks (SIEM Integration)
POST   /webhooks/elastic              # Receive Elastic SIEM alerts
POST   /webhooks/sentinel             # Receive Azure Sentinel alerts
POST   /webhooks/splunk               # Receive Splunk alerts
```

### WebSocket endpoints

```yaml
# WebSocket Connections
WS     /ws/alerts                     # Real-time alert stream
WS     /ws/incidents/{id}             # Incident updates
WS     /ws/dashboard                  # Dashboard metric updates

# Message Format
{
  "type": "alert_created" | "alert_updated" | "metric_update",
  "payload": { ... },
  "timestamp": "2026-01-15T10:30:00Z"
}
```

### Sample API response structures

```json
// GET /api/v1/incidents/{id}
{
  "id": 12345,
  "ticket_number": "INC-2026-00123",
  "title": "Ransomware Detection on WORKSTATION-042",
  "severity": "critical",
  "status": "investigating",
  "assigned_analyst": {
    "id": 5,
    "name": "John Doe",
    "email": "jdoe@company.com"
  },
  "observables": [
    {"type": "ip", "value": "203.0.113.50", "tlp": "amber"},
    {"type": "hash_sha256", "value": "e3b0c44...", "tlp": "red"}
  ],
  "affected_assets": [
    {"hostname": "WORKSTATION-042", "ip": "192.168.1.42", "criticality": "high"}
  ],
  "mitre_mapping": [
    {"tactic": "Impact", "technique_id": "T1486", "technique_name": "Data Encrypted for Impact"}
  ],
  "timeline": [
    {"timestamp": "2026-01-15T10:00:00Z", "action": "created", "actor": "SIEM Automation"},
    {"timestamp": "2026-01-15T10:05:00Z", "action": "assigned", "actor": "John Doe"}
  ],
  "sla": {
    "first_response_due": "2026-01-15T10:15:00Z",
    "first_response_met": true,
    "resolution_due": "2026-01-15T14:00:00Z"
  }
}
```

---

## Elastic SIEM integration specifications

### Deployment architecture

Deploy a multi-tier Elasticsearch cluster for production SOC workloads:

- **Hot Tier**: 3+ data nodes, 64GB RAM, SSDs, 10-day retention
- **Warm Tier**: 3+ data nodes, 64GB RAM, HDDs, 30-90 day retention  
- **Cold/Frozen**: Object storage (S3/Azure Blob), 1+ year retention
- **Fleet Server**: Agent management, scale based on endpoint count

### Webhook connector configuration for ticketing

```json
{
  "name": "SOC_Ticketing_Webhook",
  "connector_type_id": ".webhook",
  "config": {
    "url": "https://soc-app.example.com/api/v1/webhooks/elastic",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer {{secrets.api_key}}"
    }
  }
}
```

### Alert webhook payload template

```json
{
  "rule_name": "{{rule.name}}",
  "alert_id": "{{context.alerts.0._id}}",
  "severity": "{{context.rule.severity}}",
  "risk_score": "{{context.rule.risk_score}}",
  "timestamp": "{{context.alerts.0.kibana.alert.last_detected}}",
  "description": "{{context.rule.description}}",
  "host": "{{context.alerts.0.host.name}}",
  "source_ip": "{{context.alerts.0.source.ip}}",
  "destination_ip": "{{context.alerts.0.destination.ip}}",
  "user": "{{context.alerts.0.user.name}}",
  "mitre_tactic": "{{context.rule.threat.0.tactic.name}}",
  "mitre_technique": "{{context.rule.threat.0.technique.0.id}}",
  "raw_event": {{{context.alerts}}}
}
```

### Essential detection rule categories

| Category | Purpose | Query Language |
|----------|---------|----------------|
| **Initial Access** | Phishing, exploitation | KQL |
| **Execution** | PowerShell, command interpreters | EQL (sequence) |
| **Persistence** | Registry modifications, scheduled tasks | KQL |
| **Credential Access** | Brute force, credential dumping | Threshold rules |
| **Lateral Movement** | RDP, SMB, WinRM abuse | EQL correlation |
| **Exfiltration** | Large data transfers, DNS tunneling | ML anomaly |

### ILM policy for security data

```json
{
  "policy": {
    "phases": {
      "hot": {"actions": {"rollover": {"max_age": "7d", "max_primary_shard_size": "50gb"}}},
      "warm": {"min_age": "7d", "actions": {"shrink": {"number_of_shards": 1}}},
      "cold": {"min_age": "30d", "actions": {"searchable_snapshot": {"snapshot_repository": "soc-snapshots"}}},
      "frozen": {"min_age": "90d", "actions": {"searchable_snapshot": {"snapshot_repository": "cold-storage"}}},
      "delete": {"min_age": "365d", "actions": {"delete": {}}}
    }
  }
}
```

---

## Multi-cloud monitoring integration

### Cloud-specific requirements

| Cloud | Log Source | Streaming Service | Authentication |
|-------|------------|-------------------|----------------|
| **Azure** | Azure Monitor/Sentinel | Event Hubs (AMQP) | Service Principal + OAuth |
| **AWS** | CloudWatch/CloudTrail/Security Hub | Kinesis Firehose | IAM Role Assumption |
| **GCP** | Cloud Logging/Chronicle | Pub/Sub (gRPC) | Service Account |
| **OCI** | OCI Logging/Cloud Guard | OCI Streaming (Kafka) | Instance Principal |

### Data normalization with OCSF

Use Open Cybersecurity Schema Framework (OCSF) for cross-cloud event normalization:

```json
{
  "ocsf": {
    "class_uid": 3002,
    "class_name": "Authentication",
    "category_uid": 3,
    "activity_id": 1,
    "severity_id": 2,
    "actor": {
      "user": {"name": "john.doe@example.com", "uid": "user-12345"}
    },
    "src_endpoint": {"ip": "192.168.1.100"},
    "dst_endpoint": {"ip": "10.0.0.5"},
    "time": "2026-01-15T10:30:00Z",
    "cloud": {
      "provider": "aws",
      "region": "us-east-1",
      "account_uid": "123456789012"
    }
  }
}
```

---

## MITRE ATT&CK navigator integration

### Layer generation API

```python
from mitreattack.navlayers import Layer, Technique
import json

def generate_coverage_layer(coverage_data: dict) -> dict:
    """Generate ATT&CK Navigator layer from coverage data."""
    layer = Layer()
    layer.name = "SOC Detection Coverage"
    layer.domain = "enterprise-attack"
    layer.gradient = {
        "colors": ["#ff6666", "#ffe766", "#8ec843"],
        "minValue": 0,
        "maxValue": 100
    }
    
    for technique_id, data in coverage_data.items():
        tech = Technique()
        tech.techniqueID = technique_id
        tech.score = data.get('coverage_score', 0)
        tech.comment = f"Rules: {data.get('rule_count', 0)}"
        tech.metadata = [
            {"name": "Visibility", "value": str(data.get('visibility', 0))},
            {"name": "Detection", "value": str(data.get('detection', 0))}
        ]
        layer.techniques.append(tech)
    
    return layer.to_dict()
```

### Coverage scoring methodology

| Visibility Score | Meaning |
|-----------------|---------|
| 0 | No visibility - logs not collected |
| 1 | Minimal - some logs, poor quality |
| 2 | Medium - logs collected, moderate quality |
| 3 | High - comprehensive logging |
| 4 | Excellent - complete visibility with context |

| Detection Score | Meaning |
|-----------------|---------|
| -1 | Detection disabled/broken |
| 0 | No detection capability |
| 1 | Basic signature only |
| 2 | Fair - some behavioral detection |
| 3 | Good - behavioral with context |
| 4 | Very Good - ML-enhanced |
| 5 | Excellent - comprehensive, low false positives |

---

## UI/UX design specifications

### Material Design 3 color tokens

```css
/* Light Mode */
--md-sys-color-primary: #006493;
--md-sys-color-surface: #F8F9FA;
--md-sys-color-on-surface: #191C1E;

/* Dark Mode (Recommended for SOC) */
--md-sys-color-background: #1F1F1F;
--md-sys-color-surface: #2D2D2D;
--md-sys-color-on-surface: rgba(255, 255, 255, 0.87);

/* SOC Severity Colors (WCAG AA Compliant) */
--severity-critical: #F44336;  /* Dark: #FF8A80 */
--severity-high: #FF9800;      /* Dark: #FFB74D */
--severity-medium: #FFC107;    /* Dark: #FFD54F */
--severity-low: #4CAF50;       /* Dark: #81C784 */
```

### Navigation structure (Google Admin pattern)

```
Primary Navigation (Left Drawer - 256dp):
├── Dashboard
├── Alerts (badge with count)
├── Incidents
├── Investigations
│   ├── Active Cases
│   └── My Assignments
├── Threat Intelligence
├── Assets
│   ├── Inventory
│   └── Vulnerabilities
├── Reports
└── Settings
```

### Key component specifications

**Alert List Row**: 72-88dp height, 4dp left severity border, hover state with 8% opacity increase

**Data Tables**: 52dp row height, 48dp checkbox column, pagination with 10/25/50/100 options

**Metric Cards**: 200dp min width, 12dp border radius, trend indicator with sparkline

**Detail Panel**: 480-720dp width (30-50% screen), slide-in animation 300ms

### Dashboard layout grid

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Logo, Search, Notifications, User Avatar            │
├────────────┬────────────────────────────────────────────────┤
│            │  [KPI Card] [KPI Card] [KPI Card] [KPI Card]  │
│ Navigation │  ──────────────────────────────────────────── │
│ Drawer     │  [Alert Trend Chart]    [Threat Map]          │
│ (256dp)    │  ──────────────────────────────────────────── │
│            │  [Critical Alerts List]                        │
│            │  [Active Incidents List]                       │
└────────────┴────────────────────────────────────────────────┘
```

---

## Testing requirements and acceptance criteria

### SAST (Static Application Security Testing)

| Tool | Configuration | CI/CD Integration |
|------|---------------|-------------------|
| **Bandit** | `-r ./src -f json -ll` | GitHub Actions, fail on high severity |
| **SonarQube** | Quality gate: 0 critical, 80% coverage | SonarCloud integration |
| **Semgrep** | `p/security-audit p/python p/owasp-top-ten` | SARIF output to GitHub Security |
| **CodeQL** | Python + JavaScript, security-extended queries | Native GitHub integration |

### DAST (Dynamic Application Security Testing)

| Tool | Scan Type | Target |
|------|-----------|--------|
| **OWASP ZAP** | Baseline + API scan | Staging environment |
| **Nuclei** | CVE detection, misconfiguration | All exposed endpoints |

```yaml
# GitHub Actions DAST Example
- name: ZAP Baseline Scan
  uses: zaproxy/action-baseline@v0.11.0
  with:
    target: '${{ env.STAGING_URL }}'
    rules_file_name: '.zap/rules.tsv'
```

### UAT acceptance criteria for SOC workflows

**Alert Triage**:
- [ ] All critical alerts display within 5 seconds of generation
- [ ] Alert assignment notifications delivered within 30 seconds
- [ ] Bulk operations handle 100+ alerts without UI freeze
- [ ] Audit trail captures all analyst actions with timestamps

**Incident Management**:
- [ ] Incident creation from alert completes in under 3 seconds
- [ ] SLA timers calculate correctly for all severity levels
- [ ] Status transitions trigger appropriate notifications
- [ ] Evidence upload with hash verification functions correctly

**Dashboard Performance**:
- [ ] Initial load completes within 3 seconds
- [ ] Real-time updates render without visible lag
- [ ] Charts handle 10,000+ data points smoothly
- [ ] Multi-monitor tear-off maintains synchronized state

### Accessibility testing (WCAG 2.2 AA)

| Requirement | Test Method | Acceptance |
|-------------|-------------|------------|
| **Color Contrast** | axe-core automated | 4.5:1 for text, 3:1 for UI |
| **Keyboard Navigation** | Manual testing | All functions accessible |
| **Screen Reader** | NVDA/VoiceOver | Proper announcements |
| **Focus Indicators** | Visual inspection | 3px+ visible outline |

```python
# Playwright + axe-core accessibility test
from playwright.sync_api import Page
from axe_playwright_python import Axe

def test_dashboard_accessibility(page: Page):
    page.goto("https://soc.example.com/dashboard")
    axe = Axe()
    results = axe.run(page)
    assert len(results["violations"]) == 0
```

---

## Security and compliance checklist

### NIST 800-53 Rev. 5 relevant controls

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| **AC-2** | Account Management | User provisioning, role management |
| **AC-3** | Access Enforcement | RBAC for SOC analyst tiers |
| **AC-7** | Failed Logon Attempts | Lockout after 5 failures |
| **AU-2** | Event Logging | Log all security events and user actions |
| **AU-9** | Audit Protection | Immutable logs, secure storage |
| **IA-2** | User Authentication | Unique IDs, MFA required |
| **IR-4** | Incident Handling | SOC workflow implementation |
| **SC-8** | Transmission Security | TLS 1.3 encryption |
| **SC-28** | Data at Rest | Encrypted database storage |
| **SI-4** | System Monitoring | Core SOC capability |

### ISO 27001:2022 relevant controls

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| **A.5.7** | Threat Intelligence | Threat feed integration |
| **A.5.24** | Incident Planning | IR procedures documented |
| **A.5.25** | Event Assessment | Alert triage procedures |
| **A.5.26** | Incident Response | Incident workflow |
| **A.5.28** | Evidence Collection | Forensic data preservation |
| **A.8.15** | Logging | Comprehensive audit logs |
| **A.8.16** | Monitoring Activities | SOC monitoring capability |

### CI/CD security pipeline

```yaml
name: Security Pipeline
jobs:
  sast:
    steps:
      - run: bandit -r ./src -f json -o bandit.json -ll
      - run: semgrep ci --sarif > semgrep.sarif
      
  dependency-scan:
    steps:
      - run: pip-audit -r requirements.txt --format json
      - run: npm audit --json
      
  dast:
    needs: [sast]
    steps:
      - uses: zaproxy/action-baseline@v0.11.0
      - run: nuclei -u $TARGET -t cves/ -severity critical,high
      
  accessibility:
    steps:
      - run: pytest tests/accessibility/ --browser chromium
      
  security-gate:
    needs: [sast, dast, accessibility]
    steps:
      - name: Fail on critical findings
        run: |
          if grep -q '"severity": "critical"' reports/*.json; then
            exit 1
          fi
```

---

## Project structure

```
soc_application/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI initialization
│   ├── config.py                   # Environment configuration
│   │
│   ├── api/v1/                     # REST API endpoints
│   │   ├── alerts.py
│   │   ├── incidents.py
│   │   ├── threat_intel.py
│   │   ├── attack.py               # MITRE ATT&CK
│   │   ├── dashboard.py
│   │   └── webhooks.py             # SIEM webhook receivers
│   │
│   ├── websocket/                  # Real-time handlers
│   │   ├── manager.py              # Connection manager
│   │   ├── handlers.py             # WebSocket endpoints
│   │   └── pubsub.py               # Redis pub/sub
│   │
│   ├── core/
│   │   ├── security.py             # JWT, authentication
│   │   ├── events.py               # Lifespan events
│   │   └── exceptions.py
│   │
│   ├── db/
│   │   ├── base.py                 # Async engine
│   │   ├── session.py
│   │   ├── elasticsearch.py
│   │   └── repositories/
│   │
│   ├── models/                     # SQLAlchemy models
│   │   ├── incident.py
│   │   ├── alert.py
│   │   ├── observable.py
│   │   ├── attack.py               # MITRE ATT&CK
│   │   └── user.py
│   │
│   ├── schemas/                    # Pydantic schemas
│   │
│   └── services/                   # Business logic
│       ├── alert_service.py
│       ├── incident_service.py
│       ├── correlation_engine.py
│       ├── attack_service.py       # ATT&CK Navigator
│       └── notification_service.py
│
├── frontend/                       # React + MUI
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   ├── Alerts/
│   │   │   ├── Incidents/
│   │   │   └── ThreatIntel/
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   └── store/
│   └── package.json
│
├── tests/
│   ├── test_api/
│   ├── test_websocket/
│   ├── test_accessibility/
│   └── conftest.py
│
├── alembic/                        # Database migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Startup and configuration

### Environment variables

```bash
# .env configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/soc_db
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200

# Server configuration
HOST=0.0.0.0
PORT=8000                           # Configurable port
WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External integrations
ELASTIC_SIEM_URL=https://elastic.example.com
AZURE_TENANT_ID=xxx
AWS_REGION=us-east-1
```

### Launch command

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start application on configurable port
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4
```

---

## Implementation priorities

### Phase 1: Core platform (weeks 1-4)
- FastAPI backend with authentication
- PostgreSQL schema implementation
- Basic alert and incident CRUD APIs
- React frontend with dashboard layout
- WebSocket real-time alert streaming

### Phase 2: SIEM integration (weeks 5-6)
- Elastic SIEM webhook integration
- Alert ingestion and normalization
- Detection rule management
- Basic correlation engine

### Phase 3: Advanced features (weeks 7-8)
- MITRE ATT&CK mapping and Navigator
- Multi-cloud monitoring connectors
- Threat intelligence integration
- Playbook execution tracking

### Phase 4: Polish and compliance (weeks 9-10)
- WCAG 2.2 AA accessibility compliance
- Security testing (SAST/DAST)
- Performance optimization
- Documentation and deployment guides

---

This requirements document provides Claude Code with comprehensive specifications to build a production-ready SOC application. All feature specifications derive from competitor analysis of Detect Solutions, Cyfax.ai, SOCRadar, and NTT Data, combined with industry standards for SIEM integration, compliance, and security testing.