"""Incident Pydantic schemas."""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class IncidentBase(BaseModel):
    """Base incident schema."""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    severity: str = Field(..., pattern="^(critical|high|medium|low|informational)$")
    category: Optional[str] = Field(None, max_length=50)
    detection_source: Optional[str] = Field(None, max_length=100)
    business_impact: Optional[str] = Field(None, pattern="^(critical|high|medium|low|none)$")


class IncidentCreate(IncidentBase):
    """Schema for creating incidents."""
    source_alert_id: Optional[str] = None
    source_system: Optional[str] = None
    assigned_analyst_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    playbook_id: Optional[int] = None
    tags: Optional[Dict[str, Any]] = None


class IncidentUpdate(BaseModel):
    """Schema for updating incidents."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low|informational)$")
    status: Optional[str] = Field(
        None,
        pattern="^(new|assigned|investigating|contained|eradicated|recovered|closed|reopened)$"
    )
    assigned_analyst_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    business_impact: Optional[str] = None
    playbook_id: Optional[int] = None
    playbook_status: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None


class IncidentResponse(IncidentBase):
    """Schema for incident responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    status: str
    source_alert_id: Optional[str] = None
    source_system: Optional[str] = None
    assigned_analyst_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    first_response_at: Optional[datetime] = None
    containment_at: Optional[datetime] = None
    resolution_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    sla_breach: bool
    sla_first_response_due: Optional[datetime] = None
    sla_resolution_due: Optional[datetime] = None
    playbook_id: Optional[int] = None
    playbook_status: Optional[str] = None
    created_by: Optional[int] = None
    tags: Optional[Dict[str, Any]] = None


class IncidentListResponse(BaseModel):
    """Paginated incident list response."""
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int
    pages: int
