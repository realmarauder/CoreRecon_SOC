"""
Detection Rule Models - Custom detection rules and YARA/Sigma rules
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON as JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class DetectionRule(Base):
    """
    Custom detection rules for threat hunting and alerting.
    """
    __tablename__ = "detection_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(255), unique=True, nullable=False, index=True)  # rule-001, sigma-002
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Rule type and format
    rule_type = Column(String(50), nullable=False, index=True)
    # Types: sigma, yara, custom, snort, suricata, eql, kql

    rule_content = Column(Text, nullable=False)  # The actual rule definition
    rule_format = Column(String(20), nullable=False)  # yaml, text, json

    # Classification
    severity = Column(String(20), nullable=False, index=True)  # critical, high, medium, low, info
    category = Column(String(100), nullable=False, index=True)  # Malware, Phishing, etc.
    tags = Column(JSONB)  # Search tags

    # MITRE ATT&CK mapping
    mitre_tactics = Column(JSONB)
    mitre_techniques = Column(JSONB)

    # Target platform/data source
    platforms = Column(JSONB)  # Windows, Linux, macOS, AWS, Azure, etc.
    data_sources = Column(JSONB)  # process_creation, network_connection, etc.

    # Detection metadata
    false_positive_rate = Column(String(20))  # low, medium, high
    detection_methodology = Column(Text)  # How the detection works
    references = Column(JSONB)  # URLs to threat reports, CVEs, etc.

    # Status and deployment
    is_enabled = Column(Boolean, default=False, index=True)
    is_validated = Column(Boolean, default=False)
    deployed_to = Column(JSONB)  # List of SIEM platforms where deployed

    # Performance metrics
    alert_count_24h = Column(Integer, default=0)
    alert_count_7d = Column(Integer, default=0)
    true_positive_rate = Column(Integer)  # Percentage
    last_triggered_at = Column(DateTime)

    # Version control
    version = Column(String(20), nullable=False, default="1.0.0")
    changelog = Column(JSONB)  # Version history

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])


class RuleTuning(Base):
    """
    Track detection rule tuning and threshold adjustments.
    """
    __tablename__ = "rule_tunings"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("detection_rules.id"), nullable=False, index=True)

    # Tuning details
    tuning_type = Column(String(50), nullable=False)  # threshold, exclusion, scope
    previous_config = Column(JSONB)
    new_config = Column(JSONB)
    reason = Column(Text, nullable=False)

    # Impact tracking
    false_positive_reduction = Column(Integer)  # Percentage
    alert_volume_change = Column(Integer)  # Percentage change

    applied_at = Column(DateTime, server_default=func.now(), nullable=False)
    applied_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    rule = relationship("DetectionRule")
    analyst = relationship("User", foreign_keys=[applied_by])
