"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.events import close_db_connection, connect_to_db
from app.websocket.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await connect_to_db()

    # Set up Redis for WebSocket pub/sub if URL is configured
    if settings.redis_url:
        await manager.setup_redis(settings.redis_url)

    yield

    # Shutdown
    await manager.close_redis()
    await close_db_connection()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise-grade Security Operations Center (SOC) platform with real-time threat detection, incident management, and SIEM integration",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CoreRecon SOC API",
        "version": settings.app_version,
        "status": "operational",
        "features": [
            "Real-time alert streaming via WebSocket",
            "Incident management with SLA tracking",
            "SIEM webhook integration (Elastic, Sentinel, Splunk)",
            "Dashboard metrics and KPIs",
            "JWT authentication",
            "MITRE ATT&CK Navigator integration",
            "Playbook automation and execution tracking",
            "Alert correlation and deduplication"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.env
        }
    )


@app.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "connections": manager.get_connection_stats(),
        "redis_connected": manager.redis_client is not None
    }


# Import and include routers
from app.api.v1 import alerts, incidents, auth, webhooks, dashboard, mitre_attack, playbooks, correlation
from app.websocket import handlers

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["Incidents"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(mitre_attack.router, prefix="/api/v1", tags=["MITRE ATT&CK"])
app.include_router(playbooks.router, prefix="/api/v1", tags=["Playbooks"])
app.include_router(correlation.router, prefix="/api/v1", tags=["Correlation"])
app.include_router(handlers.router, tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
