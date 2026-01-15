"""
Alert Correlation and Deduplication Service
"""
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert import Alert
import hashlib
import json


class AlertCorrelationService:
    """Service for correlating related alerts and detecting alert storms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_correlated_alerts(
        self,
        alert: Alert,
        time_window_minutes: int = 60,
        max_results: int = 50
    ) -> List[Alert]:
        """
        Find alerts correlated with the given alert.

        Correlation factors:
        - Same source IP or destination IP
        - Same affected hostname
        - Same MITRE techniques
        - Same observables/IOCs
        - Same malware family
        - Temporal proximity
        """
        # Time window for correlation
        start_time = alert.created_at - timedelta(minutes=time_window_minutes)
        end_time = alert.created_at + timedelta(minutes=time_window_minutes)

        # Build correlation query
        query = select(Alert).where(
            and_(
                Alert.id != alert.id,
                Alert.created_at >= start_time,
                Alert.created_at <= end_time
            )
        )

        result = await self.db.execute(query)
        candidate_alerts = result.scalars().all()

        # Score each alert for correlation
        correlated_alerts = []
        for candidate in candidate_alerts:
            score = self._calculate_correlation_score(alert, candidate)
            if score > 0.3:  # Correlation threshold
                candidate.correlation_score = score  # Add dynamic attribute
                correlated_alerts.append(candidate)

        # Sort by correlation score
        correlated_alerts.sort(key=lambda x: x.correlation_score, reverse=True)

        return correlated_alerts[:max_results]

    def _calculate_correlation_score(self, alert1: Alert, alert2: Alert) -> float:
        """Calculate correlation score between two alerts (0.0 to 1.0)."""
        score = 0.0
        factors = 0

        # Source IP match (weight: 0.25)
        if self._extract_source_ip(alert1) and self._extract_source_ip(alert1) == self._extract_source_ip(alert2):
            score += 0.25
        factors += 1

        # Destination IP match (weight: 0.20)
        if self._extract_dest_ip(alert1) and self._extract_dest_ip(alert1) == self._extract_dest_ip(alert2):
            score += 0.20
        factors += 1

        # Hostname match (weight: 0.25)
        if self._extract_hostname(alert1) and self._extract_hostname(alert1) == self._extract_hostname(alert2):
            score += 0.25
        factors += 1

        # MITRE technique overlap (weight: 0.15)
        technique_overlap = self._calculate_technique_overlap(alert1, alert2)
        score += technique_overlap * 0.15
        factors += 1

        # Observable overlap (weight: 0.10)
        observable_overlap = self._calculate_observable_overlap(alert1, alert2)
        score += observable_overlap * 0.10
        factors += 1

        # Same category (weight: 0.05)
        if alert1.category and alert1.category == alert2.category:
            score += 0.05
        factors += 1

        return score

    def _extract_source_ip(self, alert: Alert) -> Optional[str]:
        """Extract source IP from alert."""
        if alert.raw_event and isinstance(alert.raw_event, dict):
            return (
                alert.raw_event.get("source_ip") or
                alert.raw_event.get("src_ip") or
                alert.raw_event.get("source", {}).get("ip")
            )
        return None

    def _extract_dest_ip(self, alert: Alert) -> Optional[str]:
        """Extract destination IP from alert."""
        if alert.raw_event and isinstance(alert.raw_event, dict):
            return (
                alert.raw_event.get("destination_ip") or
                alert.raw_event.get("dest_ip") or
                alert.raw_event.get("destination", {}).get("ip")
            )
        return None

    def _extract_hostname(self, alert: Alert) -> Optional[str]:
        """Extract hostname from alert."""
        if alert.raw_event and isinstance(alert.raw_event, dict):
            return (
                alert.raw_event.get("hostname") or
                alert.raw_event.get("host") or
                alert.raw_event.get("computer_name")
            )
        return None

    def _calculate_technique_overlap(self, alert1: Alert, alert2: Alert) -> float:
        """Calculate MITRE technique overlap ratio."""
        if not alert1.mitre_techniques or not alert2.mitre_techniques:
            return 0.0

        techniques1 = set()
        for tech in alert1.mitre_techniques:
            tech_id = tech.get("technique_id") if isinstance(tech, dict) else tech
            if tech_id:
                techniques1.add(tech_id)

        techniques2 = set()
        for tech in alert2.mitre_techniques:
            tech_id = tech.get("technique_id") if isinstance(tech, dict) else tech
            if tech_id:
                techniques2.add(tech_id)

        if not techniques1 or not techniques2:
            return 0.0

        overlap = len(techniques1 & techniques2)
        total = len(techniques1 | techniques2)

        return overlap / total if total > 0 else 0.0

    def _calculate_observable_overlap(self, alert1: Alert, alert2: Alert) -> float:
        """Calculate observable/IOC overlap ratio."""
        if not alert1.observables or not alert2.observables:
            return 0.0

        observables1 = set()
        for obs in alert1.observables:
            if isinstance(obs, dict):
                value = obs.get("value")
                if value:
                    observables1.add(value)

        observables2 = set()
        for obs in alert2.observables:
            if isinstance(obs, dict):
                value = obs.get("value")
                if value:
                    observables2.add(value)

        if not observables1 or not observables2:
            return 0.0

        overlap = len(observables1 & observables2)
        total = len(observables1 | observables2)

        return overlap / total if total > 0 else 0.0


class AlertDeduplicationService:
    """Service for detecting and handling duplicate alerts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_duplicate(
        self,
        alert: Alert,
        time_window_minutes: int = 60
    ) -> Optional[Alert]:
        """
        Find duplicate of the given alert within time window.

        An alert is considered a duplicate if:
        - Same alert signature/rule
        - Same source and destination
        - Same observables
        - Within time window
        """
        # Calculate deduplication hash
        alert_hash = self._calculate_alert_hash(alert)

        # Check for existing alert with same hash
        start_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        query = select(Alert).where(
            and_(
                Alert.created_at >= start_time,
                Alert.status != "closed"
            )
        )

        result = await self.db.execute(query)
        candidates = result.scalars().all()

        for candidate in candidates:
            if candidate.id != alert.id:
                candidate_hash = self._calculate_alert_hash(candidate)
                if candidate_hash == alert_hash:
                    return candidate

        return None

    def _calculate_alert_hash(self, alert: Alert) -> str:
        """
        Calculate deduplication hash for an alert.

        Hash is based on:
        - Alert title/signature
        - Source IP
        - Destination IP
        - Hostname
        - Primary observables
        """
        hash_components = {
            "title": alert.title or "",
            "source": alert.source or "",
            "source_ip": self._extract_source_ip(alert) or "",
            "dest_ip": self._extract_dest_ip(alert) or "",
            "hostname": self._extract_hostname(alert) or "",
            "observables": self._extract_primary_observables(alert)
        }

        # Create deterministic JSON string
        hash_string = json.dumps(hash_components, sort_keys=True)

        # Calculate SHA256 hash
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _extract_source_ip(self, alert: Alert) -> Optional[str]:
        """Extract source IP from alert."""
        if alert.raw_event and isinstance(alert.raw_event, dict):
            return (
                alert.raw_event.get("source_ip") or
                alert.raw_event.get("src_ip") or
                alert.raw_event.get("source", {}).get("ip")
            )
        return None

    def _extract_dest_ip(self, alert: Alert) -> Optional[str]:
        """Extract destination IP from alert."""
        if alert.raw_event and isinstance(alert.raw_event, dict):
            return (
                alert.raw_event.get("destination_ip") or
                alert.raw_event.get("dest_ip") or
                alert.raw_event.get("destination", {}).get("ip")
            )
        return None

    def _extract_hostname(self, alert: Alert) -> Optional[str]:
        """Extract hostname from alert."""
        if alert.raw_event and isinstance(alert.raw_event, dict):
            return (
                alert.raw_event.get("hostname") or
                alert.raw_event.get("host") or
                alert.raw_event.get("computer_name")
            )
        return None

    def _extract_primary_observables(self, alert: Alert) -> List[str]:
        """Extract primary observables for deduplication."""
        observables = []

        if alert.observables and isinstance(alert.observables, list):
            for obs in alert.observables[:5]:  # Top 5 observables
                if isinstance(obs, dict):
                    value = obs.get("value")
                    if value:
                        observables.append(value)

        return sorted(observables)  # Sort for consistency

    async def merge_duplicate_alerts(
        self,
        original_alert_id: int,
        duplicate_alert_id: int
    ) -> Alert:
        """
        Merge duplicate alert into original.

        - Increment duplicate count on original
        - Update timestamps
        - Close duplicate alert
        """
        # Get both alerts
        original_query = select(Alert).where(Alert.id == original_alert_id)
        original_result = await self.db.execute(original_query)
        original = original_result.scalar_one_or_none()

        duplicate_query = select(Alert).where(Alert.id == duplicate_alert_id)
        duplicate_result = await self.db.execute(duplicate_query)
        duplicate = duplicate_result.scalar_one_or_none()

        if not original or not duplicate:
            raise ValueError("Alert not found")

        # Update original alert metadata
        if not original.raw_event.get("duplicate_count"):
            original.raw_event["duplicate_count"] = 0
        original.raw_event["duplicate_count"] += 1

        if not original.raw_event.get("duplicate_alert_ids"):
            original.raw_event["duplicate_alert_ids"] = []
        original.raw_event["duplicate_alert_ids"].append(duplicate_alert_id)

        # Close duplicate
        duplicate.status = "closed"
        duplicate.description = (duplicate.description or "") + f"\n[Merged into alert {original_alert_id}]"

        await self.db.commit()
        await self.db.refresh(original)

        return original
