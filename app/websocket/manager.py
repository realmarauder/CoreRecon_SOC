"""WebSocket connection manager with Redis pub/sub support."""

import json
import logging
from typing import Dict, List, Set

from fastapi import WebSocket
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts messages.

    Supports both single-instance and distributed deployments via Redis pub/sub.
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "alerts": set(),
            "incidents": set(),
            "dashboard": set(),
        }
        self.redis_client: Redis = None
        self.redis_pubsub = None

    async def connect(self, websocket: WebSocket, channel: str = "alerts"):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            channel: Channel name (alerts, incidents, dashboard)
        """
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = set()

        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket connected to channel '{channel}'. Total connections: {len(self.active_connections[channel])}")

    def disconnect(self, websocket: WebSocket, channel: str = "alerts"):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            channel: Channel name
        """
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            logger.info(f"WebSocket disconnected from channel '{channel}'. Remaining connections: {len(self.active_connections[channel])}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: dict, channel: str = "alerts"):
        """
        Broadcast a message to all connections in a channel.

        Args:
            message: Message dictionary to broadcast
            channel: Channel name
        """
        if channel not in self.active_connections:
            logger.warning(f"Channel '{channel}' not found")
            return

        message_text = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.active_connections[channel].discard(connection)

    async def broadcast_alert(self, alert_data: dict):
        """
        Broadcast an alert to all alert channel subscribers.

        Args:
            alert_data: Alert data dictionary
        """
        message = {
            "type": "alert_created",
            "payload": alert_data,
            "timestamp": alert_data.get("created_at")
        }
        await self.broadcast(message, channel="alerts")

        # Also publish to Redis for distributed instances
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "soc:alerts",
                    json.dumps(message)
                )
            except Exception as e:
                logger.error(f"Error publishing to Redis: {e}")

    async def broadcast_incident(self, incident_data: dict):
        """
        Broadcast an incident update to all incident channel subscribers.

        Args:
            incident_data: Incident data dictionary
        """
        message = {
            "type": "incident_updated",
            "payload": incident_data,
            "timestamp": incident_data.get("updated_at")
        }
        await self.broadcast(message, channel="incidents")

        # Publish to Redis
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "soc:incidents",
                    json.dumps(message)
                )
            except Exception as e:
                logger.error(f"Error publishing to Redis: {e}")

    async def broadcast_metric_update(self, metrics: dict):
        """
        Broadcast dashboard metrics update.

        Args:
            metrics: Metrics data dictionary
        """
        from datetime import datetime

        message = {
            "type": "metric_update",
            "payload": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message, channel="dashboard")

        # Publish to Redis
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "soc:dashboard",
                    json.dumps(message)
                )
            except Exception as e:
                logger.error(f"Error publishing to Redis: {e}")

    async def setup_redis(self, redis_url: str):
        """
        Set up Redis connection for pub/sub.

        Args:
            redis_url: Redis connection URL
        """
        try:
            self.redis_client = Redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis connection established for WebSocket pub/sub")

            # Set up pub/sub subscription
            await self._subscribe_to_redis()

        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None

    async def _subscribe_to_redis(self):
        """Subscribe to Redis pub/sub channels for distributed broadcasting."""
        if not self.redis_client:
            return

        try:
            self.redis_pubsub = self.redis_client.pubsub()
            await self.redis_pubsub.subscribe(
                "soc:alerts",
                "soc:incidents",
                "soc:dashboard"
            )

            logger.info("✅ Subscribed to Redis pub/sub channels")

        except Exception as e:
            logger.error(f"❌ Failed to subscribe to Redis: {e}")

    async def listen_to_redis(self):
        """
        Listen for Redis pub/sub messages and broadcast to local connections.

        This should be run as a background task.
        """
        if not self.redis_pubsub:
            return

        logger.info("🎧 Listening for Redis pub/sub messages...")

        async for message in self.redis_pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                channel = message["channel"]
                data = json.loads(message["data"])

                # Map Redis channels to WebSocket channels
                channel_map = {
                    "soc:alerts": "alerts",
                    "soc:incidents": "incidents",
                    "soc:dashboard": "dashboard"
                }

                ws_channel = channel_map.get(channel)
                if ws_channel:
                    await self.broadcast(data, channel=ws_channel)

            except Exception as e:
                logger.error(f"Error processing Redis message: {e}")

    async def close_redis(self):
        """Close Redis connections."""
        if self.redis_pubsub:
            await self.redis_pubsub.unsubscribe()
            await self.redis_pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Redis connections closed")

    def get_connection_stats(self) -> dict:
        """
        Get current connection statistics.

        Returns:
            Dictionary with connection counts per channel
        """
        return {
            channel: len(connections)
            for channel, connections in self.active_connections.items()
        }


# Global WebSocket manager instance
manager = WebSocketManager()
