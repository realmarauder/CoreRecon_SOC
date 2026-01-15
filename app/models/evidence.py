"""Evidence model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Evidence(Base):
    """Evidence with chain of custody model."""

    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    filename = Column(String(255))
    file_path = Column(String(500))
    file_hash_sha256 = Column(String(64), index=True)
    file_hash_md5 = Column(String(32))
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    description = Column(Text)

    # Chain of custody
    collected_by = Column(Integer, ForeignKey("users.id"))
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    chain_of_custody = Column(JSONB, comment="Array of custody transfer records")

    # Storage
    storage_location = Column(String(255))
    storage_type = Column(String(50), comment="local, s3, azure_blob, etc.")

    # Metadata
    tags = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="evidence")

    def __repr__(self):
        return f"<Evidence(id={self.id}, filename='{self.filename}', hash='{self.file_hash_sha256[:16]}...')>"
