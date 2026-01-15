"""
Playbook Models - SOC automation playbooks and execution tracking
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON as JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Playbook(Base):
    """
    Playbook template for automated response actions.
    """
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)  # Malware, Phishing, DDoS, etc.
    severity = Column(String(20), index=True)  # critical, high, medium, low

    # Playbook definition
    steps = Column(JSONB, nullable=False)  # Array of step definitions
    mitre_tactics = Column(JSONB)  # Associated MITRE ATT&CK tactics
    mitre_techniques = Column(JSONB)  # Associated MITRE ATT&CK techniques

    # Automation settings
    auto_trigger = Column(Boolean, default=False)  # Auto-execute on matching incidents
    trigger_conditions = Column(JSONB)  # Conditions for auto-trigger
    approval_required = Column(Boolean, default=True)  # Require human approval

    # Metadata
    version = Column(String(20), nullable=False, default="1.0.0")
    is_active = Column(Boolean, default=True, index=True)
    tags = Column(JSONB)  # Search tags

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    executions = relationship("PlaybookExecution", back_populates="playbook", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class PlaybookExecution(Base):
    """
    Track playbook execution instances.
    """
    __tablename__ = "playbook_executions"

    id = Column(Integer, primary_key=True, index=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)

    # Execution metadata
    status = Column(String(30), nullable=False, default="pending", index=True)
    # Statuses: pending, running, paused, completed, failed, cancelled

    # Execution data
    current_step = Column(Integer, default=0)  # Current step index
    step_results = Column(JSONB)  # Results from each step
    variables = Column(JSONB)  # Runtime variables

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Human interaction
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    playbook = relationship("Playbook", back_populates="executions")
    incident = relationship("Incident", back_populates="playbook_executions")
    triggerer = relationship("User", foreign_keys=[triggered_by])
    approver = relationship("User", foreign_keys=[approved_by])
