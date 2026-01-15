"""Alert Pydantic schemas."""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class AlertBase(BaseModel):
    """Base alert schema."""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    severity: str = Field(..., pattern="^(critical|high|medium|low|informational)$")
    source: Optional[str] = Field(None, max_length=100)
    detection_rule_id: Optional[str] = None
    detection_rule_name: Optional[str] = None


class AlertCreate(AlertBase):
    """Schema for creating alerts."""
    alert_id: str = Field(..., max_length=255)
    raw_event: Optional[Dict[str, Any]] = None
    observables: Optional[Dict[str, Any]] = None
    affected_assets: Optional[Dict[str, Any]] = None
    mitre_tactics: Optional[Dict[str, Any]] = None
    mitre_techniques: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None


class AlertUpdate(BaseModel):
    """Schema for updating alerts."""
    status: Optional[str] = Field(None, pattern="^(new|acknowledged|investigating|resolved|false_positive|suppressed)$")
    assigned_to: Optional[int] = None
    notes: Optional[str] = None
    false_positive_reason: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None


class AlertResponse(AlertBase):
    """Schema for alert responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: str
    status: str
    source_alert_id: Optional[str] = None
    raw_event: Optional[Dict[str, Any]] = None
    observables: Optional[Dict[str, Any]] = None
    affected_assets: Optional[Dict[str, Any]] = None
    mitre_tactics: Optional[Dict[str, Any]] = None
    mitre_techniques: Optional[Dict[str, Any]] = None
    assigned_to: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    escalated_to_incident_id: Optional[int] = None
    detected_at: datetime
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    tags: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class AlertListResponse(BaseModel):
    """Paginated alert list response."""
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
    pages: int
