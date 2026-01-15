"""Alert model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class Alert(Base):
    """Security alert model."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(
        String(20),
        nullable=False,
        index=True,
        comment="critical, high, medium, low, informational"
    )
    status = Column(
        String(30),
        nullable=False,
        default="new",
        index=True,
        comment="new, acknowledged, investigating, resolved, false_positive, suppressed"
    )
    source = Column(String(100), comment="SIEM, EDR, Cloud, Manual")
    source_alert_id = Column(String(255))
    detection_rule_id = Column(String(100))
    detection_rule_name = Column(String(255))

    # Alert data
    raw_event = Column(JSONB, comment="Original event data")
    observables = Column(JSONB, comment="IOCs and observables")
    affected_assets = Column(JSONB, comment="Affected hosts, users, etc.")

    # MITRE ATT&CK mapping
    mitre_tactics = Column(JSONB)
    mitre_techniques = Column(JSONB)

    # Assignment and tracking
    assigned_to = Column(Integer)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(Integer)
    escalated_to_incident_id = Column(Integer)

    # Timestamps
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)

    # Metadata
    tags = Column(JSONB)
    notes = Column(Text)
    false_positive_reason = Column(Text)

    def __repr__(self):
        return f"<Alert(id={self.id}, severity='{self.severity}', status='{self.status}')>"
