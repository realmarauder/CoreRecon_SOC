"""Dashboard metrics and KPI endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.alert import Alert
from app.models.incident import Incident

router = APIRouter()


@router.get("/metrics")
async def get_dashboard_metrics(
    time_range: int = Query(24, description="Time range in hours"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard KPI metrics.

    Args:
        time_range: Time range in hours (default: 24)
        db: Database session

    Returns:
        Dashboard metrics including alert counts, incident stats, and trends
    """
    now = datetime.utcnow()
    start_time = now - timedelta(hours=time_range)

    # Alert metrics
    total_alerts_query = select(func.count()).select_from(Alert)
    total_alerts_result = await db.execute(total_alerts_query)
    total_alerts = total_alerts_result.scalar() or 0

    # Recent alerts
    recent_alerts_query = select(func.count()).select_from(Alert).where(
        Alert.created_at >= start_time
    )
    recent_alerts_result = await db.execute(recent_alerts_query)
    recent_alerts = recent_alerts_result.scalar() or 0

    # Alerts by severity
    severity_query = select(
        Alert.severity,
        func.count(Alert.id).label("count")
    ).where(
        Alert.created_at >= start_time
    ).group_by(Alert.severity)

    severity_result = await db.execute(severity_query)
    alerts_by_severity = {row.severity: row.count for row in severity_result}

    # Alerts by status
    status_query = select(
        Alert.status,
        func.count(Alert.id).label("count")
    ).where(
        Alert.created_at >= start_time
    ).group_by(Alert.status)

    status_result = await db.execute(status_query)
    alerts_by_status = {row.status: row.count for row in status_result}

    # Incident metrics
    total_incidents_query = select(func.count()).select_from(Incident)
    total_incidents_result = await db.execute(total_incidents_query)
    total_incidents = total_incidents_result.scalar() or 0

    # Open incidents
    open_incidents_query = select(func.count()).select_from(Incident).where(
        Incident.status.in_(["new", "assigned", "investigating", "contained"])
    )
    open_incidents_result = await db.execute(open_incidents_query)
    open_incidents = open_incidents_result.scalar() or 0

    # Critical incidents
    critical_incidents_query = select(func.count()).select_from(Incident).where(
        Incident.severity == "critical",
        Incident.status != "closed"
    )
    critical_incidents_result = await db.execute(critical_incidents_query)
    critical_incidents = critical_incidents_result.scalar() or 0

    # SLA breaches
    sla_breach_query = select(func.count()).select_from(Incident).where(
        Incident.sla_breach == True,
        Incident.created_at >= start_time
    )
    sla_breach_result = await db.execute(sla_breach_query)
    sla_breaches = sla_breach_result.scalar() or 0

    # Mean Time to Respond (MTTR) - incidents with first_response_at
    mttr_query = select(
        func.avg(
            func.extract('epoch', Incident.first_response_at - Incident.created_at)
        )
    ).where(
        Incident.first_response_at.isnot(None),
        Incident.created_at >= start_time
    )
    mttr_result = await db.execute(mttr_query)
    mttr_seconds = mttr_result.scalar() or 0
    mttr_minutes = round(mttr_seconds / 60, 2) if mttr_seconds else 0

    # Mean Time to Resolve (MTTR) - incidents with resolution_at
    mttresolve_query = select(
        func.avg(
            func.extract('epoch', Incident.resolution_at - Incident.created_at)
        )
    ).where(
        Incident.resolution_at.isnot(None),
        Incident.created_at >= start_time
    )
    mttresolve_result = await db.execute(mttresolve_query)
    mttresolve_seconds = mttresolve_result.scalar() or 0
    mttresolve_hours = round(mttresolve_seconds / 3600, 2) if mttresolve_seconds else 0

    return {
        "timestamp": now.isoformat(),
        "time_range_hours": time_range,
        "alerts": {
            "total": total_alerts,
            "recent": recent_alerts,
            "by_severity": {
                "critical": alerts_by_severity.get("critical", 0),
                "high": alerts_by_severity.get("high", 0),
                "medium": alerts_by_severity.get("medium", 0),
                "low": alerts_by_severity.get("low", 0),
                "informational": alerts_by_severity.get("informational", 0)
            },
            "by_status": alerts_by_status
        },
        "incidents": {
            "total": total_incidents,
            "open": open_incidents,
            "critical": critical_incidents,
            "sla_breaches": sla_breaches
        },
        "performance": {
            "mean_time_to_respond_minutes": mttr_minutes,
            "mean_time_to_resolve_hours": mttresolve_hours
        }
    }


@router.get("/alerts/trend")
async def get_alert_trend(
    hours: int = Query(24, description="Time range in hours"),
    interval: int = Query(1, description="Interval in hours"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get alert trend data for charting.

    Args:
        hours: Time range in hours
        interval: Data point interval in hours
        db: Database session

    Returns:
        Time-series alert trend data
    """
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)

    # Generate time buckets
    buckets = []
    current_time = start_time
    while current_time <= now:
        bucket_start = current_time
        bucket_end = current_time + timedelta(hours=interval)

        # Count alerts in this time bucket
        count_query = select(func.count()).select_from(Alert).where(
            Alert.created_at >= bucket_start,
            Alert.created_at < bucket_end
        )
        count_result = await db.execute(count_query)
        count = count_result.scalar() or 0

        buckets.append({
            "timestamp": bucket_start.isoformat(),
            "count": count
        })

        current_time = bucket_end

    return {
        "time_range_hours": hours,
        "interval_hours": interval,
        "data": buckets
    }


@router.get("/threats/map")
async def get_threat_map(
    hours: int = Query(24, description="Time range in hours"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get geographic threat map data.

    Args:
        hours: Time range in hours
        db: Database session

    Returns:
        Geographic threat data for visualization
    """
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)

    # This would typically extract IP addresses from alerts and geolocate them
    # For now, return sample data structure
    return {
        "time_range_hours": hours,
        "threats": [
            # Sample data - in production, this would come from alert IP geolocation
            # {
            #     "latitude": 40.7128,
            #     "longitude": -74.0060,
            #     "count": 15,
            #     "severity": "high",
            #     "country": "United States"
            # }
        ],
        "note": "Geographic threat mapping requires IP geolocation service integration"
    }
