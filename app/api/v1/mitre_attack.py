"""
MITRE ATT&CK Navigator Integration API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.base import get_db
from app.models.alert import Alert
from app.models.incident import Incident
from app.core.security import get_current_active_user
from app.models.user import User


router = APIRouter(prefix="/mitre", tags=["MITRE ATT&CK"])


@router.get("/navigator/layer")
async def get_mitre_navigator_layer(
    time_range: int = Query(30, ge=1, le=365, description="Time range in days"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate MITRE ATT&CK Navigator layer JSON from alerts and incidents.

    Returns a Layer 4.5 format JSON for visualization in ATT&CK Navigator.
    """
    start_date = datetime.utcnow() - timedelta(days=time_range)

    # Query alerts for MITRE techniques
    query = select(Alert).where(Alert.created_at >= start_date)

    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)

    result = await db.execute(query)
    alerts = result.scalars().all()

    # Aggregate MITRE techniques with counts
    technique_counts = {}
    tactic_counts = {}

    for alert in alerts:
        if alert.mitre_techniques:
            for technique in alert.mitre_techniques:
                technique_id = technique.get("technique_id") if isinstance(technique, dict) else technique
                if technique_id:
                    technique_counts[technique_id] = technique_counts.get(technique_id, 0) + 1

        if alert.mitre_tactics:
            for tactic in alert.mitre_tactics:
                tactic_name = tactic.get("tactic") if isinstance(tactic, dict) else tactic
                if tactic_name:
                    tactic_counts[tactic_name] = tactic_counts.get(tactic_name, 0) + 1

    # Calculate max count for color gradient
    max_count = max(technique_counts.values()) if technique_counts else 1

    # Build Navigator layer JSON
    techniques = []
    for technique_id, count in technique_counts.items():
        # Color gradient based on frequency (white to red)
        score = count / max_count
        color = _calculate_color(score)

        techniques.append({
            "techniqueID": technique_id,
            "score": count,
            "color": color,
            "comment": f"Detected {count} time(s) in last {time_range} days",
            "enabled": True,
            "metadata": [
                {"name": "count", "value": str(count)},
                {"name": "time_range", "value": f"{time_range} days"}
            ]
        })

    layer = {
        "name": f"CoreRecon SOC - Last {time_range} Days",
        "versions": {
            "attack": "15",
            "navigator": "4.9.6",
            "layer": "4.5"
        },
        "domain": "enterprise-attack",
        "description": f"MITRE ATT&CK coverage based on CoreRecon SOC detections from {start_date.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}",
        "filters": {
            "platforms": ["windows", "linux", "macos", "network", "cloud"]
        },
        "sorting": 3,
        "layout": {
            "layout": "side",
            "aggregateFunction": "average",
            "showID": False,
            "showName": True,
            "showAggregateScores": True,
            "countUnscored": False
        },
        "hideDisabled": False,
        "techniques": techniques,
        "gradient": {
            "colors": ["#ffffff", "#ff6666"],
            "minValue": 0,
            "maxValue": max_count
        },
        "legendItems": [
            {"label": "High Frequency", "color": "#ff6666"},
            {"label": "Medium Frequency", "color": "#ffb3b3"},
            {"label": "Low Frequency", "color": "#ffe6e6"}
        ],
        "metadata": [
            {"name": "Generated", "value": datetime.utcnow().isoformat()},
            {"name": "Total Alerts", "value": str(len(alerts))},
            {"name": "Unique Techniques", "value": str(len(technique_counts))},
            {"name": "Time Range", "value": f"{time_range} days"}
        ]
    }

    return layer


@router.get("/coverage/statistics")
async def get_mitre_coverage_statistics(
    time_range: int = Query(30, ge=1, le=365, description="Time range in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get MITRE ATT&CK coverage statistics.
    """
    start_date = datetime.utcnow() - timedelta(days=time_range)

    # Get total alerts with MITRE mapping
    alert_query = select(func.count(Alert.id)).where(
        Alert.created_at >= start_date,
        Alert.mitre_techniques.isnot(None)
    )
    result = await db.execute(alert_query)
    total_mapped_alerts = result.scalar() or 0

    # Get alerts
    alerts_result = await db.execute(
        select(Alert).where(Alert.created_at >= start_date)
    )
    alerts = alerts_result.scalars().all()

    # Aggregate statistics
    unique_techniques = set()
    unique_tactics = set()
    technique_frequency = {}
    tactic_frequency = {}

    for alert in alerts:
        if alert.mitre_techniques:
            for technique in alert.mitre_techniques:
                tech_id = technique.get("technique_id") if isinstance(technique, dict) else technique
                if tech_id:
                    unique_techniques.add(tech_id)
                    technique_frequency[tech_id] = technique_frequency.get(tech_id, 0) + 1

        if alert.mitre_tactics:
            for tactic in alert.mitre_tactics:
                tactic_name = tactic.get("tactic") if isinstance(tactic, dict) else tactic
                if tactic_name:
                    unique_tactics.add(tactic_name)
                    tactic_frequency[tactic_name] = tactic_frequency.get(tactic_name, 0) + 1

    # Top 10 techniques
    top_techniques = sorted(
        technique_frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    # Top 10 tactics
    top_tactics = sorted(
        tactic_frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    return {
        "time_range_days": time_range,
        "total_alerts": len(alerts),
        "alerts_with_mitre_mapping": total_mapped_alerts,
        "unique_techniques_detected": len(unique_techniques),
        "unique_tactics_detected": len(unique_tactics),
        "top_techniques": [
            {"technique_id": tech, "count": count}
            for tech, count in top_techniques
        ],
        "top_tactics": [
            {"tactic": tactic, "count": count}
            for tactic, count in top_tactics
        ],
        "coverage_percentage": round(
            (len(unique_techniques) / 600) * 100, 2  # ~600 techniques in ATT&CK
        ) if unique_techniques else 0
    }


@router.get("/techniques/{technique_id}/alerts")
async def get_alerts_by_technique(
    technique_id: str,
    time_range: int = Query(30, ge=1, le=365, description="Time range in days"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all alerts associated with a specific MITRE ATT&CK technique.
    """
    start_date = datetime.utcnow() - timedelta(days=time_range)

    # Query alerts containing the technique
    # Using JSONB contains operator
    query = select(Alert).where(
        Alert.created_at >= start_date,
        Alert.mitre_techniques.isnot(None)
    )

    result = await db.execute(query)
    all_alerts = result.scalars().all()

    # Filter alerts containing the technique ID
    filtered_alerts = []
    for alert in all_alerts:
        if alert.mitre_techniques:
            for technique in alert.mitre_techniques:
                tech_id = technique.get("technique_id") if isinstance(technique, dict) else technique
                if tech_id == technique_id:
                    filtered_alerts.append(alert)
                    break

    total = len(filtered_alerts)

    # Pagination
    offset = (page - 1) * page_size
    paginated_alerts = filtered_alerts[offset : offset + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "technique_id": technique_id,
        "alerts": [
            {
                "id": alert.id,
                "alert_id": alert.alert_id,
                "title": alert.title,
                "severity": alert.severity,
                "status": alert.status,
                "source": alert.source,
                "created_at": alert.created_at,
                "mitre_techniques": alert.mitre_techniques,
                "mitre_tactics": alert.mitre_tactics
            }
            for alert in paginated_alerts
        ]
    }


def _calculate_color(score: float) -> str:
    """
    Calculate color based on frequency score (0.0 to 1.0).
    Returns hex color from white to red.
    """
    # RGB gradient from white (255,255,255) to red (255,0,0)
    red = 255
    green = int(255 * (1 - score))
    blue = int(255 * (1 - score))

    return f"#{red:02x}{green:02x}{blue:02x}"
