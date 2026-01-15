"""WebSocket endpoint handlers."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert streaming.

    Clients connect to this endpoint to receive real-time alert updates.

    Message Format:
        {
            "type": "alert_created" | "alert_updated",
            "payload": { ... alert data ... },
            "timestamp": "2026-01-15T10:30:00Z"
        }

    Args:
        websocket: WebSocket connection
    """
    await manager.connect(websocket, channel="alerts")

    try:
        # Send welcome message
        await manager.send_personal_message(
            '{"type":"connected","message":"Connected to alert stream"}',
            websocket
        )

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await manager.send_personal_message(
                '{"type":"pong"}',
                websocket
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="alerts")
        logger.info("Client disconnected from alerts stream")
    except Exception as e:
        logger.error(f"WebSocket error in alerts stream: {e}")
        manager.disconnect(websocket, channel="alerts")


@router.websocket("/ws/incidents/{incident_id}")
async def websocket_incident(websocket: WebSocket, incident_id: int):
    """
    WebSocket endpoint for incident-specific updates.

    Clients connect to receive real-time updates for a specific incident.

    Args:
        websocket: WebSocket connection
        incident_id: Incident ID to monitor
    """
    channel = f"incident_{incident_id}"

    # Create channel if it doesn't exist
    if channel not in manager.active_connections:
        manager.active_connections[channel] = set()

    await manager.connect(websocket, channel=channel)

    try:
        await manager.send_personal_message(
            f'{{"type":"connected","message":"Connected to incident {incident_id} stream"}}',
            websocket
        )

        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(
                '{"type":"pong"}',
                websocket
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel=channel)
        logger.info(f"Client disconnected from incident {incident_id} stream")
    except Exception as e:
        logger.error(f"WebSocket error in incident {incident_id} stream: {e}")
        manager.disconnect(websocket, channel=channel)


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for dashboard metric updates.

    Clients connect to receive real-time dashboard metrics and KPIs.

    Message Format:
        {
            "type": "metric_update",
            "payload": {
                "total_alerts": 1234,
                "critical_alerts": 45,
                "open_incidents": 12,
                ...
            },
            "timestamp": "2026-01-15T10:30:00Z"
        }

    Args:
        websocket: WebSocket connection
    """
    await manager.connect(websocket, channel="dashboard")

    try:
        await manager.send_personal_message(
            '{"type":"connected","message":"Connected to dashboard stream"}',
            websocket
        )

        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(
                '{"type":"pong"}',
                websocket
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="dashboard")
        logger.info("Client disconnected from dashboard stream")
    except Exception as e:
        logger.error(f"WebSocket error in dashboard stream: {e}")
        manager.disconnect(websocket, channel="dashboard")
