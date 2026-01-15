# CoreRecon SOC - System Architecture

## Overview

CoreRecon SOC is built on a modern, scalable architecture designed for high-performance security operations. The system follows a microservices-inspired approach with clear separation of concerns.

## Architecture Layers

### 1. Presentation Layer
- **Technology**: React 18+ with TypeScript
- **UI Framework**: Material-UI v5 (Material Design 3)
- **State Management**: Redux Toolkit
- **Real-time Communication**: WebSocket hooks

### 2. API Layer
- **Framework**: FastAPI (async-first)
- **API Style**: RESTful + WebSocket
- **Authentication**: JWT with OAuth2
- **Rate Limiting**: Redis-based
- **Documentation**: OpenAPI 3.0 (Swagger/ReDoc)

### 3. Business Logic Layer
- **Services**: Modular service architecture
- **Key Services**:
  - Alert Service (triage, correlation)
  - Incident Service (lifecycle management)
  - Threat Intel Service (IOC management)
  - MITRE ATT&CK Service (framework integration)
  - Notification Service (multi-channel alerts)

### 4. Data Layer
- **Primary Database**: PostgreSQL 14+ (relational data)
- **Time-Series**: TimescaleDB extension (metrics)
- **Search Engine**: Elasticsearch 8.x (log analytics)
- **Cache**: Redis 7+ (session, pub/sub)

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + MUI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Dashboard │  │ Alerts   │  │Incidents │  │Threat    │       │
│  │          │  │          │  │          │  │Intel     │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────┬───────────────────────────────────────────────────┘
              │
              │ HTTPS/WSS
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                   API Gateway (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Authentication Middleware (JWT Validation)              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ REST API     │  │ WebSocket    │  │ Webhooks     │         │
│  │ Endpoints    │  │ Handlers     │  │ (SIEM)       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────┬───────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                  Business Logic Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Alert    │  │Incident  │  │Threat    │  │ MITRE    │       │
│  │ Service  │  │ Service  │  │Intel Svc │  │ATT&CK Svc│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────┬───────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                   Data Access Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          SQLAlchemy Async ORM (Repository Pattern)       │   │
│  └──────────────────────────────────────────────────────────┘   │
└───┬──────────┬────────────┬────────────────────────────────┬────┘
    │          │            │                                │
┌───▼──┐  ┌───▼────┐  ┌────▼────────┐  ┌──────────────────▼──────┐
│Postgre│  │Redis   │  │Elasticsearch│  │    External APIs        │
│SQL+TS │  │        │  │             │  │  (Cloud, Threat Intel)  │
└───────┘  └────────┘  └─────────────┘  └─────────────────────────┘
```

## Data Flow

### Alert Ingestion Flow
1. **Webhook Reception**: SIEM sends alert via webhook to `/api/v1/webhooks/elastic`
2. **Validation**: Request validated, authenticated
3. **Normalization**: Alert data normalized to OCSF schema
4. **Storage**: Stored in PostgreSQL + Elasticsearch
5. **Pub/Sub**: Published to Redis channel
6. **WebSocket Broadcast**: Real-time delivery to connected clients
7. **SLA Timer**: Background worker initiates SLA tracking

### Incident Management Flow
1. **Creation**: Alert escalated to incident or manually created
2. **Assignment**: Auto-assigned or manually assigned to analyst
3. **Investigation**: Analyst adds observables, evidence, timeline entries
4. **MITRE Mapping**: Techniques mapped to incident
5. **Response**: Playbook execution, containment actions
6. **Resolution**: Incident closed with resolution details
7. **Post-Incident**: Metrics aggregated, lessons learned documented

## Security Architecture

### Authentication & Authorization
```
User Request
    ↓
HTTPS/TLS 1.3
    ↓
API Gateway
    ↓
JWT Validation ←─── Redis Session Cache
    ↓
RBAC Check (User Roles)
    ↓
Endpoint Handler
```

### Encryption
- **In Transit**: TLS 1.3 for all communications
- **At Rest**: PostgreSQL transparent data encryption
- **Secrets**: Environment variables, HashiCorp Vault (optional)

## Scalability Strategy

### Horizontal Scaling
- **Backend**: Stateless FastAPI instances behind load balancer
- **WebSocket**: Redis pub/sub for message distribution across instances
- **Database**: PostgreSQL read replicas for query scaling
- **Elasticsearch**: Multi-node cluster with hot/warm/cold tiers

### Vertical Scaling
- **Database Tuning**: Connection pooling (20 connections/instance)
- **Cache Strategy**: Redis for frequently accessed data
- **Query Optimization**: Database indexes on critical paths

## High Availability

### Fault Tolerance
- **Database**: PostgreSQL streaming replication (primary + 2 replicas)
- **Cache**: Redis Sentinel for automatic failover
- **Elasticsearch**: 3-node cluster with replication
- **Application**: Multi-instance deployment with health checks

### Disaster Recovery
- **Backup Strategy**:
  - PostgreSQL: Continuous archiving + daily base backups
  - Elasticsearch: Snapshot to object storage (daily)
  - Redis: AOF persistence + snapshots
- **RTO**: < 1 hour
- **RPO**: < 5 minutes

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| API Response Time (p95) | < 200ms | TBD |
| WebSocket Latency | < 2 seconds | TBD |
| Concurrent WebSocket Connections | 3,200+ | TBD |
| Database Query Time (p95) | < 100ms | TBD |
| Alert Throughput | 10,000/minute | TBD |

## Technology Decisions

### Why FastAPI?
- **Performance**: 2,847 req/s vs Django's 1,205 req/s
- **Async Support**: Native async/await for I/O-bound operations
- **Type Safety**: Pydantic validation reduces bugs
- **Auto Documentation**: OpenAPI spec generation

### Why PostgreSQL + TimescaleDB?
- **Reliability**: ACID compliance, battle-tested
- **Time-Series**: TimescaleDB provides 20x faster aggregations
- **JSON Support**: Native JSONB for flexible schemas
- **Ecosystem**: Rich tooling, extensions, monitoring

### Why Elasticsearch?
- **Search Performance**: Inverted index for full-text search
- **Scalability**: Horizontal scaling for massive log volumes
- **ML Capabilities**: Anomaly detection, threat hunting
- **Elastic SIEM**: Native integration

### Why Redis?
- **Speed**: In-memory, microsecond latency
- **Pub/Sub**: Real-time message distribution
- **Data Structures**: Lists, sets, sorted sets for caching
- **Persistence**: AOF + RDB for durability

## Deployment Architecture

### Production Environment
```
                        ┌──────────────┐
                        │ Load Balancer │
                        │   (NGINX)     │
                        └───────┬──────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
        │FastAPI       │ │FastAPI     │ │FastAPI     │
        │Instance 1    │ │Instance 2  │ │Instance 3  │
        └──────┬───────┘ └─────┬──────┘ └─────┬──────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
        ┌───────▼──────┐ ┌────▼─────┐ ┌─────▼────────┐
        │ PostgreSQL   │ │  Redis   │ │Elasticsearch │
        │  Cluster     │ │ Sentinel │ │   Cluster    │
        └──────────────┘ └──────────┘ └──────────────┘
```

## Monitoring & Observability

### Metrics
- **Application**: Prometheus + Grafana
- **Infrastructure**: Node Exporter, cAdvisor
- **Database**: PostgreSQL Exporter, pg_stat_statements

### Logging
- **Application Logs**: Structured JSON (structlog)
- **Access Logs**: NGINX access logs
- **Audit Logs**: Immutable audit trail in PostgreSQL

### Tracing
- **Distributed Tracing**: OpenTelemetry (future enhancement)
- **Request IDs**: Correlation IDs for request tracking

## Future Enhancements

1. **Kubernetes Deployment**: Container orchestration for auto-scaling
2. **Machine Learning**: Anomaly detection, threat prediction
3. **GraphQL API**: Alternative API for complex queries
4. **Event Sourcing**: CQRS pattern for audit trail
5. **Multi-Tenancy**: Isolated environments for MSP deployments

---

**Last Updated**: January 2026
**Version**: 1.0.0
