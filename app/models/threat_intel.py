"""
Threat Intelligence Models - External threat feeds and indicators
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON as JSONB, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ThreatFeed(Base):
    """
    External threat intelligence feed configuration.
    """
    __tablename__ = "threat_feeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    provider = Column(String(100), nullable=False)  # MISP, OpenCTI, AlienVault, etc.
    feed_type = Column(String(50), nullable=False)  # ioc, malware, vulnerability, actor

    # Connection details
    url = Column(String(512), nullable=False)
    api_key_encrypted = Column(Text)  # Encrypted API key
    auth_method = Column(String(50))  # api_key, oauth, basic, none

    # Feed settings
    is_enabled = Column(Boolean, default=True, index=True)
    poll_interval_minutes = Column(Integer, default=60)  # How often to fetch
    last_poll_at = Column(DateTime)
    next_poll_at = Column(DateTime)

    # Quality metrics
    reliability_score = Column(Float)  # 0.0 to 1.0
    total_indicators_imported = Column(Integer, default=0)
    active_indicators = Column(Integer, default=0)

    # Configuration
    filter_config = Column(JSONB)  # Filters for what to import
    tags = Column(JSONB)  # Classification tags

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    indicators = relationship("ThreatIndicator", back_populates="feed", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class ThreatIndicator(Base):
    """
    Threat intelligence indicator (IOC) from external feeds.
    """
    __tablename__ = "threat_indicators"

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("threat_feeds.id"), nullable=False, index=True)

    # Indicator details
    indicator_type = Column(String(50), nullable=False, index=True)
    # Types: ip, domain, url, hash_md5, hash_sha1, hash_sha256, email, file_path, registry_key

    value = Column(String(512), nullable=False, index=True)
    description = Column(Text)

    # Classification
    threat_type = Column(String(100), index=True)  # malware, phishing, c2, exploit
    malware_family = Column(String(100), index=True)  # Emotet, Cobalt Strike, etc.
    tags = Column(JSONB)

    # MITRE ATT&CK mapping
    mitre_tactics = Column(JSONB)
    mitre_techniques = Column(JSONB)

    # Confidence and severity
    confidence_score = Column(Float)  # 0.0 to 1.0
    severity = Column(String(20), index=True)  # critical, high, medium, low
    tlp = Column(String(20), default="amber")  # TLP classification

    # Context
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    source_references = Column(JSONB)  # URLs to original reports
    related_campaigns = Column(JSONB)  # APT groups, campaigns

    # Status
    is_active = Column(Boolean, default=True, index=True)
    expiration_date = Column(DateTime)
    false_positive = Column(Boolean, default=False)

    # Matching statistics
    match_count = Column(Integer, default=0)  # How many times matched in alerts
    last_matched_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    feed = relationship("ThreatFeed", back_populates="indicators")


class ThreatActor(Base):
    """
    Known threat actors and APT groups.
    """
    __tablename__ = "threat_actors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    aliases = Column(JSONB)  # Alternative names

    description = Column(Text)
    motivation = Column(String(100))  # financial, espionage, ideology, etc.
    sophistication = Column(String(50))  # low, medium, high, expert

    # Attribution
    suspected_origin = Column(String(100))  # Country or region
    targets = Column(JSONB)  # Industries, countries targeted

    # TTPs
    mitre_tactics = Column(JSONB)
    mitre_techniques = Column(JSONB)
    tools_used = Column(JSONB)  # Malware, exploits used

    # Activity
    first_observed = Column(DateTime)
    last_observed = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # References
    references = Column(JSONB)  # Threat reports, URLs

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
