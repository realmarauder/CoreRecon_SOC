"""
Alert Correlation and Deduplication API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.base import get_db
from app.models.alert import Alert
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.correlation import AlertCorrelationService, AlertDeduplicationService


router = APIRouter(prefix="/correlation", tags=["Alert Correlation"])


@router.get("/alerts/{alert_id}/correlated")
async def get_correlated_alerts(
    alert_id: int,
    time_window_minutes: int = Query(60, ge=1, le=1440, description="Time window in minutes"),
    max_results: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Find alerts correlated with the given alert.

    Correlation is based on:
    - Common source/destination IPs
    - Common affected hosts
    - Overlapping MITRE ATT&CK techniques
    - Shared observables/IOCs
    - Temporal proximity
    """
    # Get the alert
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )

    # Find correlated alerts
    correlation_service = AlertCorrelationService(db)
    correlated_alerts = await correlation_service.find_correlated_alerts(
        alert,
        time_window_minutes=time_window_minutes,
        max_results=max_results
    )

    return {
        "alert_id": alert_id,
        "time_window_minutes": time_window_minutes,
        "total_correlated": len(correlated_alerts),
        "correlated_alerts": [
            {
                "id": alert.id,
                "alert_id": alert.alert_id,
                "title": alert.title,
                "severity": alert.severity,
                "status": alert.status,
                "source": alert.source,
                "created_at": alert.created_at,
                "correlation_score": round(alert.correlation_score, 3),
                "mitre_techniques": alert.mitre_techniques,
            }
            for alert in correlated_alerts
        ]
    }


@router.post("/alerts/{alert_id}/find-duplicate")
async def find_duplicate_alert(
    alert_id: int,
    time_window_minutes: int = Query(60, ge=1, le=1440, description="Time window in minutes"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Check if an alert is a duplicate of an existing alert.

    Returns the original alert if a duplicate is found.
    """
    # Get the alert
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )

    # Find duplicate
    dedup_service = AlertDeduplicationService(db)
    duplicate = await dedup_service.find_duplicate(
        alert,
        time_window_minutes=time_window_minutes
    )

    if duplicate:
        return {
            "is_duplicate": True,
            "original_alert": {
                "id": duplicate.id,
                "alert_id": duplicate.alert_id,
                "title": duplicate.title,
                "severity": duplicate.severity,
                "status": duplicate.status,
                "created_at": duplicate.created_at,
                "duplicate_count": duplicate.raw_event.get("duplicate_count", 0) if duplicate.raw_event else 0
            }
        }
    else:
        return {
            "is_duplicate": False,
            "original_alert": None
        }


@router.post("/alerts/{original_id}/merge/{duplicate_id}")
async def merge_duplicate_alerts(
    original_id: int,
    duplicate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Merge a duplicate alert into the original alert.

    This will:
    - Increment duplicate count on original
    - Close the duplicate alert
    - Link duplicate to original
    """
    # Get both alerts
    original_query = select(Alert).where(Alert.id == original_id)
    original_result = await db.execute(original_query)
    original = original_result.scalar_one_or_none()

    duplicate_query = select(Alert).where(Alert.id == duplicate_id)
    duplicate_result = await db.execute(duplicate_query)
    duplicate = duplicate_result.scalar_one_or_none()

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Original alert {original_id} not found"
        )

    if not duplicate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Duplicate alert {duplicate_id} not found"
        )

    # Merge
    dedup_service = AlertDeduplicationService(db)
    merged_alert = await dedup_service.merge_duplicate_alerts(original_id, duplicate_id)

    return {
        "message": "Alerts merged successfully",
        "original_alert": {
            "id": merged_alert.id,
            "alert_id": merged_alert.alert_id,
            "title": merged_alert.title,
            "duplicate_count": merged_alert.raw_event.get("duplicate_count", 0) if merged_alert.raw_event else 0
        }
    }


@router.get("/statistics")
async def get_correlation_statistics(
    time_range_hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get alert correlation and deduplication statistics.
    """
    from datetime import datetime, timedelta

    start_time = datetime.utcnow() - timedelta(hours=time_range_hours)

    # Get total alerts
    total_query = select(Alert).where(Alert.created_at >= start_time)
    total_result = await db.execute(total_query)
    all_alerts = total_result.scalars().all()

    total_alerts = len(all_alerts)

    # Count deduplicated alerts
    duplicates = 0
    for alert in all_alerts:
        if alert.raw_event and alert.raw_event.get("duplicate_count"):
            duplicates += alert.raw_event.get("duplicate_count", 0)

    # Calculate correlation potential (alerts with shared IPs/hosts)
    # This is a simplified calculation
    source_ips = set()
    dest_ips = set()
    hostnames = set()

    for alert in all_alerts:
        if alert.raw_event and isinstance(alert.raw_event, dict):
            if alert.raw_event.get("source_ip"):
                source_ips.add(alert.raw_event["source_ip"])
            if alert.raw_event.get("destination_ip"):
                dest_ips.add(alert.raw_event["destination_ip"])
            if alert.raw_event.get("hostname"):
                hostnames.add(alert.raw_event["hostname"])

    return {
        "time_range_hours": time_range_hours,
        "total_alerts": total_alerts,
        "unique_alerts": total_alerts - duplicates,
        "duplicate_alerts_merged": duplicates,
        "deduplication_rate": round((duplicates / total_alerts * 100), 2) if total_alerts > 0 else 0,
        "unique_source_ips": len(source_ips),
        "unique_dest_ips": len(dest_ips),
        "unique_hostnames": len(hostnames),
        "correlation_potential": {
            "by_source_ip": len(source_ips),
            "by_dest_ip": len(dest_ips),
            "by_hostname": len(hostnames)
        }
    }
