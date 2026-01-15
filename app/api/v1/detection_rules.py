"""
Detection Rule Management API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.detection_rule import DetectionRule, RuleTuning
from app.schemas.detection_rule import (
    DetectionRuleCreate,
    DetectionRuleUpdate,
    DetectionRuleResponse,
    DetectionRuleListResponse,
    RuleTuningCreate,
)
from app.core.security import get_current_active_user
from app.models.user import User


router = APIRouter(prefix="/detection-rules", tags=["Detection Rules"])


@router.get("/", response_model=DetectionRuleListResponse)
async def list_detection_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    rule_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    is_validated: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all detection rules with pagination and filtering."""
    query = select(DetectionRule)

    if rule_type:
        query = query.where(DetectionRule.rule_type == rule_type)
    if category:
        query = query.where(DetectionRule.category == category)
    if severity:
        query = query.where(DetectionRule.severity == severity)
    if is_enabled is not None:
        query = query.where(DetectionRule.is_enabled == is_enabled)
    if is_validated is not None:
        query = query.where(DetectionRule.is_validated == is_validated)

    # Get total count
    count_query = select(func.count()).select_from(DetectionRule)
    if rule_type:
        count_query = count_query.where(DetectionRule.rule_type == rule_type)
    if category:
        count_query = count_query.where(DetectionRule.category == category)
    if severity:
        count_query = count_query.where(DetectionRule.severity == severity)
    if is_enabled is not None:
        count_query = count_query.where(DetectionRule.is_enabled == is_enabled)
    if is_validated is not None:
        count_query = count_query.where(DetectionRule.is_validated == is_validated)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rules = result.scalars().all()

    return DetectionRuleListResponse(
        total=total,
        page=page,
        page_size=page_size,
        rules=rules
    )


@router.get("/{rule_id}", response_model=DetectionRuleResponse)
async def get_detection_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detection rule by ID."""
    query = select(DetectionRule).where(DetectionRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection rule {rule_id} not found"
        )

    return rule


@router.post("/", response_model=DetectionRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_detection_rule(
    rule_in: DetectionRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new detection rule."""
    # Check if rule_id already exists
    existing_query = select(DetectionRule).where(DetectionRule.rule_id == rule_in.rule_id)
    existing_result = await db.execute(existing_query)
    existing_rule = existing_result.scalar_one_or_none()

    if existing_rule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rule with rule_id '{rule_in.rule_id}' already exists"
        )

    rule = DetectionRule(
        **rule_in.model_dump(),
        created_by=current_user.id
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return rule


@router.patch("/{rule_id}", response_model=DetectionRuleResponse)
async def update_detection_rule(
    rule_id: int,
    rule_in: DetectionRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a detection rule."""
    query = select(DetectionRule).where(DetectionRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection rule {rule_id} not found"
        )

    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a detection rule."""
    query = select(DetectionRule).where(DetectionRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection rule {rule_id} not found"
        )

    await db.delete(rule)
    await db.commit()


@router.post("/{rule_id}/enable", response_model=DetectionRuleResponse)
async def enable_detection_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Enable a detection rule."""
    query = select(DetectionRule).where(DetectionRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection rule {rule_id} not found"
        )

    rule.is_enabled = True
    await db.commit()
    await db.refresh(rule)

    return rule


@router.post("/{rule_id}/disable", response_model=DetectionRuleResponse)
async def disable_detection_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Disable a detection rule."""
    query = select(DetectionRule).where(DetectionRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection rule {rule_id} not found"
        )

    rule.is_enabled = False
    await db.commit()
    await db.refresh(rule)

    return rule


@router.post("/{rule_id}/tune")
async def tune_detection_rule(
    rule_id: int,
    tuning_in: RuleTuningCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record rule tuning adjustment."""
    # Verify rule exists
    rule_query = select(DetectionRule).where(DetectionRule.id == rule_id)
    rule_result = await db.execute(rule_query)
    rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection rule {rule_id} not found"
        )

    tuning = RuleTuning(
        rule_id=rule_id,
        **tuning_in.model_dump(),
        applied_by=current_user.id
    )

    db.add(tuning)
    await db.commit()
    await db.refresh(tuning)

    return {
        "message": "Rule tuning recorded successfully",
        "tuning": {
            "id": tuning.id,
            "tuning_type": tuning.tuning_type,
            "reason": tuning.reason,
            "applied_at": tuning.applied_at,
            "applied_by": tuning.applied_by
        }
    }


@router.get("/{rule_id}/tunings")
async def get_rule_tunings(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all tuning history for a rule."""
    query = select(RuleTuning).where(RuleTuning.rule_id == rule_id).order_by(RuleTuning.applied_at.desc())
    result = await db.execute(query)
    tunings = result.scalars().all()

    return {
        "rule_id": rule_id,
        "total_tunings": len(tunings),
        "tunings": tunings
    }


@router.get("/statistics/overview")
async def get_detection_rule_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detection rule statistics and health metrics."""
    # Total rules
    total_query = select(func.count()).select_from(DetectionRule)
    total_result = await db.execute(total_query)
    total_rules = total_result.scalar()

    # Enabled rules
    enabled_query = select(func.count()).select_from(DetectionRule).where(DetectionRule.is_enabled == True)
    enabled_result = await db.execute(enabled_query)
    enabled_rules = enabled_result.scalar()

    # Rules by type
    type_query = select(DetectionRule.rule_type, func.count()).group_by(DetectionRule.rule_type)
    type_result = await db.execute(type_query)
    rules_by_type = {row[0]: row[1] for row in type_result}

    # Rules by severity
    severity_query = select(DetectionRule.severity, func.count()).group_by(DetectionRule.severity)
    severity_result = await db.execute(severity_query)
    rules_by_severity = {row[0]: row[1] for row in severity_result}

    return {
        "total_rules": total_rules,
        "enabled_rules": enabled_rules,
        "disabled_rules": total_rules - enabled_rules,
        "rules_by_type": rules_by_type,
        "rules_by_severity": rules_by_severity,
        "coverage": {
            "platforms": await _get_unique_platforms(db),
            "data_sources": await _get_unique_data_sources(db)
        }
    }


async def _get_unique_platforms(db: AsyncSession) -> list:
    """Get unique platforms covered by rules."""
    query = select(DetectionRule).where(DetectionRule.platforms.isnot(None))
    result = await db.execute(query)
    rules = result.scalars().all()

    platforms = set()
    for rule in rules:
        if rule.platforms:
            platforms.update(rule.platforms)

    return list(platforms)


async def _get_unique_data_sources(db: AsyncSession) -> list:
    """Get unique data sources covered by rules."""
    query = select(DetectionRule).where(DetectionRule.data_sources.isnot(None))
    result = await db.execute(query)
    rules = result.scalars().all()

    data_sources = set()
    for rule in rules:
        if rule.data_sources:
            data_sources.update(rule.data_sources)

    return list(data_sources)
