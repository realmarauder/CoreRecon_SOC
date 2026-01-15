"""
Detection Rule Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DetectionRuleCreate(BaseModel):
    """Create a new detection rule."""
    rule_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: str
    rule_content: str
    rule_format: str  # yaml, text, json
    severity: str
    category: str
    tags: Optional[List[str]] = None
    mitre_tactics: Optional[List[str]] = None
    mitre_techniques: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    data_sources: Optional[List[str]] = None
    false_positive_rate: Optional[str] = None
    detection_methodology: Optional[str] = None
    references: Optional[List[str]] = None
    is_enabled: bool = False


class DetectionRuleUpdate(BaseModel):
    """Update a detection rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_content: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    mitre_tactics: Optional[List[str]] = None
    mitre_techniques: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    data_sources: Optional[List[str]] = None
    false_positive_rate: Optional[str] = None
    detection_methodology: Optional[str] = None
    references: Optional[List[str]] = None
    is_enabled: Optional[bool] = None
    is_validated: Optional[bool] = None


class DetectionRuleResponse(BaseModel):
    """Detection rule response model."""
    id: int
    rule_id: str
    name: str
    description: Optional[str]
    rule_type: str
    rule_content: str
    rule_format: str
    severity: str
    category: str
    tags: Optional[List[str]]
    mitre_tactics: Optional[List[str]]
    mitre_techniques: Optional[List[str]]
    platforms: Optional[List[str]]
    data_sources: Optional[List[str]]
    false_positive_rate: Optional[str]
    detection_methodology: Optional[str]
    references: Optional[List[str]]
    is_enabled: bool
    is_validated: bool
    deployed_to: Optional[List[str]]
    alert_count_24h: int
    alert_count_7d: int
    true_positive_rate: Optional[int]
    last_triggered_at: Optional[datetime]
    version: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


class DetectionRuleListResponse(BaseModel):
    """List of detection rules."""
    total: int
    page: int
    page_size: int
    rules: List[DetectionRuleResponse]


class RuleTuningCreate(BaseModel):
    """Create rule tuning entry."""
    tuning_type: str  # threshold, exclusion, scope
    previous_config: dict
    new_config: dict
    reason: str
    false_positive_reduction: Optional[int] = None
    alert_volume_change: Optional[int] = None
