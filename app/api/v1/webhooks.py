"""Webhook endpoints for SIEM integrations."""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.base import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.

    Args:
        payload: Request body bytes
        signature: Signature from request header
        secret: Webhook secret key

    Returns:
        True if signature is valid
    """
    if not secret:
        logger.warning("Webhook secret not configured, skipping signature verification")
        return True

    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


@router.post("/elastic", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def elastic_siem_webhook(
    request: Request,
    x_elastic_signature: str = Header(None, alias="X-Elastic-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for Elastic SIEM alerts.

    Receives alerts from Elastic Security and creates alert records.

    Expected payload format:
        {
            "rule_name": "Suspicious PowerShell Activity",
            "alert_id": "abc123...",
            "severity": "high",
            "risk_score": 75,
            "timestamp": "2026-01-15T10:30:00Z",
            "description": "PowerShell executed with encoded command",
            "host": "WORKSTATION-042",
            "source_ip": "192.168.1.42",
            "destination_ip": "203.0.113.50",
            "user": "john.doe",
            "mitre_tactic": "Execution",
            "mitre_technique": "T1059.001",
            "raw_event": { ... }
        }

    Args:
        request: FastAPI request object
        x_elastic_signature: Webhook signature header
        db: Database session

    Returns:
        Created alert

    Raises:
        HTTPException: 401 if signature verification fails
        HTTPException: 400 if payload is invalid
    """
    # Get request body
    body = await request.body()
    payload = await request.json()

    # Verify signature
    if settings.elastic_siem_webhook_secret and x_elastic_signature:
        if not verify_webhook_signature(body, x_elastic_signature, settings.elastic_siem_webhook_secret):
            logger.warning("Invalid webhook signature from Elastic SIEM")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

    # Normalize Elastic SIEM payload to internal alert format
    try:
        alert_data = normalize_elastic_alert(payload)
    except Exception as e:
        logger.error(f"Error normalizing Elastic alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid alert payload: {str(e)}"
        )

    # Create alert
    alert = Alert(**alert_data, status="new")
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.info(f"Created alert from Elastic SIEM: {alert.alert_id}")

    # Broadcast alert to WebSocket clients
    alert_dict = {
        "id": alert.id,
        "alert_id": alert.alert_id,
        "title": alert.title,
        "severity": alert.severity,
        "status": alert.status,
        "source": alert.source,
        "created_at": alert.created_at.isoformat() if alert.created_at else None
    }
    await manager.broadcast_alert(alert_dict)

    return alert


def normalize_elastic_alert(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Elastic SIEM alert payload to internal format.

    Args:
        payload: Elastic SIEM webhook payload

    Returns:
        Normalized alert data dictionary
    """
    # Map Elastic severity to internal severity
    severity_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low"
    }

    # Extract severity from risk_score if not provided
    risk_score = payload.get("risk_score", 0)
    if risk_score >= 90:
        severity = "critical"
    elif risk_score >= 70:
        severity = "high"
    elif risk_score >= 50:
        severity = "medium"
    else:
        severity = "low"

    # Override with explicit severity if provided
    severity = severity_map.get(payload.get("severity"), severity)

    # Build observables
    observables = []
    if payload.get("source_ip"):
        observables.append({"type": "ip", "value": payload["source_ip"], "role": "source"})
    if payload.get("destination_ip"):
        observables.append({"type": "ip", "value": payload["destination_ip"], "role": "destination"})
    if payload.get("user"):
        observables.append({"type": "user_account", "value": payload["user"]})

    # Build MITRE ATT&CK mapping
    mitre_tactics = []
    mitre_techniques = []

    if payload.get("mitre_tactic"):
        mitre_tactics.append({"name": payload["mitre_tactic"]})

    if payload.get("mitre_technique"):
        mitre_techniques.append({
            "id": payload["mitre_technique"],
            "name": payload.get("mitre_technique_name", "")
        })

    # Build affected assets
    affected_assets = []
    if payload.get("host"):
        affected_assets.append({
            "type": "host",
            "hostname": payload["host"],
            "ip_address": payload.get("source_ip")
        })

    return {
        "alert_id": payload.get("alert_id", f"ELASTIC-{datetime.utcnow().timestamp()}"),
        "title": payload.get("rule_name", "Elastic SIEM Alert"),
        "description": payload.get("description"),
        "severity": severity,
        "source": "Elastic SIEM",
        "detection_rule_name": payload.get("rule_name"),
        "source_alert_id": payload.get("alert_id"),
        "raw_event": payload.get("raw_event", payload),
        "observables": {"items": observables} if observables else None,
        "affected_assets": {"items": affected_assets} if affected_assets else None,
        "mitre_tactics": {"items": mitre_tactics} if mitre_tactics else None,
        "mitre_techniques": {"items": mitre_techniques} if mitre_techniques else None,
        "detected_at": datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00")) if payload.get("timestamp") else datetime.utcnow()
    }


@router.post("/sentinel", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def azure_sentinel_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for Azure Sentinel alerts.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Created alert
    """
    payload = await request.json()

    # Normalize Azure Sentinel payload
    alert_data = normalize_sentinel_alert(payload)

    # Create alert
    alert = Alert(**alert_data, status="new")
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.info(f"Created alert from Azure Sentinel: {alert.alert_id}")

    # Broadcast to WebSocket
    alert_dict = {
        "id": alert.id,
        "alert_id": alert.alert_id,
        "title": alert.title,
        "severity": alert.severity,
        "source": alert.source,
        "created_at": alert.created_at.isoformat() if alert.created_at else None
    }
    await manager.broadcast_alert(alert_dict)

    return alert


def normalize_sentinel_alert(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Azure Sentinel alert payload to internal format.

    Args:
        payload: Azure Sentinel webhook payload

    Returns:
        Normalized alert data dictionary
    """
    severity_map = {
        "High": "high",
        "Medium": "medium",
        "Low": "low",
        "Informational": "informational"
    }

    return {
        "alert_id": payload.get("SystemAlertId", f"SENTINEL-{datetime.utcnow().timestamp()}"),
        "title": payload.get("AlertDisplayName", "Azure Sentinel Alert"),
        "description": payload.get("Description"),
        "severity": severity_map.get(payload.get("Severity"), "medium"),
        "source": "Azure Sentinel",
        "detection_rule_name": payload.get("AlertType"),
        "source_alert_id": payload.get("SystemAlertId"),
        "raw_event": payload,
        "detected_at": datetime.fromisoformat(payload["TimeGenerated"].replace("Z", "+00:00")) if payload.get("TimeGenerated") else datetime.utcnow()
    }


@router.post("/splunk", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def splunk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for Splunk alerts.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Created alert
    """
    payload = await request.json()

    # Normalize Splunk payload
    alert_data = normalize_splunk_alert(payload)

    # Create alert
    alert = Alert(**alert_data, status="new")
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.info(f"Created alert from Splunk: {alert.alert_id}")

    # Broadcast to WebSocket
    alert_dict = {
        "id": alert.id,
        "alert_id": alert.alert_id,
        "title": alert.title,
        "severity": alert.severity,
        "source": alert.source,
        "created_at": alert.created_at.isoformat() if alert.created_at else None
    }
    await manager.broadcast_alert(alert_dict)

    return alert


def normalize_splunk_alert(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Splunk alert payload to internal format.

    Args:
        payload: Splunk webhook payload

    Returns:
        Normalized alert data dictionary
    """
    severity_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "informational"
    }

    result = payload.get("result", {})

    return {
        "alert_id": payload.get("search_id", f"SPLUNK-{datetime.utcnow().timestamp()}"),
        "title": payload.get("search_name", "Splunk Alert"),
        "description": result.get("description"),
        "severity": severity_map.get(payload.get("severity", "medium").lower(), "medium"),
        "source": "Splunk",
        "detection_rule_name": payload.get("search_name"),
        "source_alert_id": payload.get("search_id"),
        "raw_event": payload,
        "detected_at": datetime.utcnow()
    }
