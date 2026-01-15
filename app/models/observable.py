"""Observable/IOC model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Observable(Base):
    """Observable/Indicator of Compromise (IOC) model."""

    __tablename__ = "observables"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        index=True
    )
    type = Column(
        String(30),
        nullable=False,
        index=True,
        comment="ip, domain, url, hash_md5, hash_sha1, hash_sha256, email, filename, registry_key, user_account, process"
    )
    value = Column(Text, nullable=False, index=True)
    tlp = Column(
        String(10),
        default="amber",
        comment="TLP: white, green, amber, red"
    )
    is_malicious = Column(Boolean)
    confidence = Column(String(20), comment="high, medium, low")
    source = Column(String(100), comment="Where the IOC was identified")

    # Timestamps
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Additional context
    context = Column(JSONB, comment="Additional metadata")
    tags = Column(JSONB)

    # Relationships
    incident = relationship("Incident", back_populates="observables")

    def __repr__(self):
        return f"<Observable(id={self.id}, type='{self.type}', value='{self.value[:50]}')>"
