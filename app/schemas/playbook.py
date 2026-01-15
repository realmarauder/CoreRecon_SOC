"""
Playbook Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Playbook Schemas
class PlaybookStepSchema(BaseModel):
    """Individual playbook step."""
    step_number: int
    name: str
    description: Optional[str] = None
    action_type: str  # manual, automated, approval
    action_config: Dict[str, Any]  # Action-specific configuration
    success_criteria: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = 300


class PlaybookCreate(BaseModel):
    """Create a new playbook."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str
    severity: Optional[str] = None
    steps: List[PlaybookStepSchema]
    mitre_tactics: Optional[List[str]] = None
    mitre_techniques: Optional[List[str]] = None
    auto_trigger: bool = False
    trigger_conditions: Optional[Dict[str, Any]] = None
    approval_required: bool = True
    tags: Optional[List[str]] = None


class PlaybookUpdate(BaseModel):
    """Update a playbook."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    steps: Optional[List[PlaybookStepSchema]] = None
    mitre_tactics: Optional[List[str]] = None
    mitre_techniques: Optional[List[str]] = None
    auto_trigger: Optional[bool] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    approval_required: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class PlaybookResponse(BaseModel):
    """Playbook response model."""
    id: int
    name: str
    description: Optional[str]
    category: str
    severity: Optional[str]
    steps: List[Dict[str, Any]]
    mitre_tactics: Optional[List[str]]
    mitre_techniques: Optional[List[str]]
    auto_trigger: bool
    trigger_conditions: Optional[Dict[str, Any]]
    approval_required: bool
    version: str
    is_active: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


# Playbook Execution Schemas
class PlaybookExecutionCreate(BaseModel):
    """Start playbook execution."""
    playbook_id: int
    incident_id: Optional[int] = None
    variables: Optional[Dict[str, Any]] = None


class PlaybookExecutionUpdate(BaseModel):
    """Update execution status."""
    status: Optional[str] = None
    current_step: Optional[int] = None
    step_results: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None


class PlaybookExecutionApprove(BaseModel):
    """Approve playbook execution."""
    approve: bool
    comment: Optional[str] = None


class PlaybookExecutionResponse(BaseModel):
    """Playbook execution response."""
    id: int
    playbook_id: int
    incident_id: Optional[int]
    status: str
    current_step: int
    step_results: Optional[Dict[str, Any]]
    variables: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    triggered_by: int
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaybookListResponse(BaseModel):
    """List of playbooks."""
    total: int
    page: int
    page_size: int
    playbooks: List[PlaybookResponse]
