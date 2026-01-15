"""Incident models."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Incident(Base):
    """Security incident model."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, nullable=False, index=True)
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
        comment="new, assigned, investigating, contained, eradicated, recovered, closed, reopened"
    )
    category = Column(String(50))
    detection_source = Column(String(100))
    source_alert_id = Column(String(255))
    source_system = Column(String(50))

    # Assignment
    assigned_analyst_id = Column(Integer, ForeignKey("users.id"))
    assigned_team_id = Column(Integer)

    # Business impact
    business_impact = Column(String(20), comment="critical, high, medium, low, none")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_response_at = Column(DateTime)
    containment_at = Column(DateTime)
    resolution_at = Column(DateTime)
    closed_at = Column(DateTime)

    # SLA tracking
    sla_breach = Column(Boolean, default=False)
    sla_first_response_due = Column(DateTime)
    sla_resolution_due = Column(DateTime)

    # Playbook
    playbook_id = Column(Integer)
    playbook_status = Column(String(30))

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    tags = Column(JSONB)
    custom_fields = Column(JSONB)

    # Relationships
    assigned_analyst = relationship(
        "User",
        back_populates="assigned_incidents",
        foreign_keys=[assigned_analyst_id]
    )
    created_by_user = relationship(
        "User",
        back_populates="created_incidents",
        foreign_keys=[created_by]
    )
    timeline = relationship(
        "IncidentTimeline",
        back_populates="incident",
        cascade="all, delete-orphan"
    )
    affected_assets = relationship(
        "AffectedAsset",
        back_populates="incident",
        cascade="all, delete-orphan"
    )
    observables = relationship(
        "Observable",
        back_populates="incident",
        cascade="all, delete-orphan"
    )
    evidence = relationship(
        "Evidence",
        back_populates="incident",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Incident(id={self.id}, ticket='{self.ticket_number}', severity='{self.severity}')>"


class IncidentTimeline(Base):
    """Incident timeline/audit log model."""

    __tablename__ = "incident_timeline"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    action_type = Column(String(50), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"))
    actor_type = Column(String(20), comment="user, system, automation")
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    incident = relationship("Incident", back_populates="timeline")

    def __repr__(self):
        return f"<IncidentTimeline(id={self.id}, incident_id={self.incident_id}, action='{self.action_type}')>"


class AffectedAsset(Base):
    """Affected assets in an incident."""

    __tablename__ = "affected_assets"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    asset_type = Column(
        String(30),
        comment="host, server, network_device, application, database, user_account, cloud_resource"
    )
    identifier = Column(String(255), nullable=False)
    hostname = Column(String(255))
    ip_address = Column(String(45))
    criticality = Column(String(20))
    owner = Column(String(100))
    department = Column(String(100))
    containment_status = Column(String(30))

    # Relationships
    incident = relationship("Incident", back_populates="affected_assets")

    def __repr__(self):
        return f"<AffectedAsset(id={self.id}, type='{self.asset_type}', identifier='{self.identifier}')>"
