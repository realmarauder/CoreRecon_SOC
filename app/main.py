"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.events import close_db_connection, connect_to_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await connect_to_db()
    yield
    # Shutdown
    await close_db_connection()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise-grade Security Operations Center (SOC) platform",
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
        "status": "operational"
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


# Import and include routers
# from app.api.v1 import alerts, incidents, auth, dashboard, attack, threat_intel, webhooks
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
# app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["Incidents"])
# app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
# app.include_router(attack.router, prefix="/api/v1/attack", tags=["MITRE ATT&CK"])
# app.include_router(threat_intel.router, prefix="/api/v1/threat-intel", tags=["Threat Intelligence"])
# app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
