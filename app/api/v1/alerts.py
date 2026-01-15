"""Alert API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertListResponse

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    db: AsyncSession = Depends(get_db),
):
    """
    List alerts with pagination and filtering.

    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: 25, max: 100)
        severity: Filter by severity level
        status: Filter by alert status
        source: Filter by detection source
        db: Database session

    Returns:
        Paginated list of alerts
    """
    # Build query
    query = select(Alert)

    # Apply filters
    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    if source:
        query = query.where(Alert.source == source)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(Alert.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    alerts = result.scalars().all()

    # Calculate total pages
    pages = (total + page_size - 1) // page_size

    return AlertListResponse(
        items=alerts,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get alert by ID.

    Args:
        alert_id: Alert database ID
        db: Database session

    Returns:
        Alert details

    Raises:
        HTTPException: 404 if alert not found
    """
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )

    return alert


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new alert.

    Args:
        alert_data: Alert creation data
        db: Database session

    Returns:
        Created alert

    Raises:
        HTTPException: 400 if alert_id already exists
    """
    # Check if alert_id already exists
    existing_query = select(Alert).where(Alert.alert_id == alert_data.alert_id)
    existing_result = await db.execute(existing_query)
    existing_alert = existing_result.scalar_one_or_none()

    if existing_alert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alert with alert_id '{alert_data.alert_id}' already exists"
        )

    # Create alert
    alert = Alert(
        **alert_data.model_dump(),
        status="new"
    )

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an alert.

    Args:
        alert_id: Alert database ID
        alert_update: Alert update data
        db: Database session

    Returns:
        Updated alert

    Raises:
        HTTPException: 404 if alert not found
    """
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )

    # Update fields
    update_data = alert_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)

    await db.commit()
    await db.refresh(alert)

    return alert


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Acknowledge an alert.

    Args:
        alert_id: Alert database ID
        db: Database session

    Returns:
        Updated alert

    Raises:
        HTTPException: 404 if alert not found
    """
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )

    from datetime import datetime
    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an alert.

    Args:
        alert_id: Alert database ID
        db: Database session

    Raises:
        HTTPException: 404 if alert not found
    """
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )

    await db.delete(alert)
    await db.commit()
