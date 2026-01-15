"""
Playbook Management and Execution API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.base import get_db
from app.models.playbook import Playbook, PlaybookExecution
from app.models.incident import Incident, IncidentTimeline
from app.schemas.playbook import (
    PlaybookCreate,
    PlaybookUpdate,
    PlaybookResponse,
    PlaybookListResponse,
    PlaybookExecutionCreate,
    PlaybookExecutionUpdate,
    PlaybookExecutionApprove,
    PlaybookExecutionResponse,
)
from app.core.security import get_current_active_user
from app.models.user import User


router = APIRouter(prefix="/playbooks", tags=["Playbooks"])


@router.get("/", response_model=PlaybookListResponse)
async def list_playbooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all playbooks with pagination and filtering."""
    query = select(Playbook)

    if category:
        query = query.where(Playbook.category == category)
    if severity:
        query = query.where(Playbook.severity == severity)
    if is_active is not None:
        query = query.where(Playbook.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(Playbook)
    if category:
        count_query = count_query.where(Playbook.category == category)
    if severity:
        count_query = count_query.where(Playbook.severity == severity)
    if is_active is not None:
        count_query = count_query.where(Playbook.is_active == is_active)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    playbooks = result.scalars().all()

    return PlaybookListResponse(
        total=total,
        page=page,
        page_size=page_size,
        playbooks=playbooks
    )


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get playbook by ID."""
    query = select(Playbook).where(Playbook.id == playbook_id)
    result = await db.execute(query)
    playbook = result.scalar_one_or_none()

    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook {playbook_id} not found"
        )

    return playbook


@router.post("/", response_model=PlaybookResponse, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    playbook_in: PlaybookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new playbook."""
    playbook = Playbook(
        **playbook_in.model_dump(),
        created_by=current_user.id
    )

    db.add(playbook)
    await db.commit()
    await db.refresh(playbook)

    return playbook


@router.patch("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: int,
    playbook_in: PlaybookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a playbook."""
    query = select(Playbook).where(Playbook.id == playbook_id)
    result = await db.execute(query)
    playbook = result.scalar_one_or_none()

    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook {playbook_id} not found"
        )

    update_data = playbook_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(playbook, field, value)

    await db.commit()
    await db.refresh(playbook)

    return playbook


@router.delete("/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a playbook."""
    query = select(Playbook).where(Playbook.id == playbook_id)
    result = await db.execute(query)
    playbook = result.scalar_one_or_none()

    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook {playbook_id} not found"
        )

    await db.delete(playbook)
    await db.commit()


# Playbook Execution Endpoints

@router.post("/execute", response_model=PlaybookExecutionResponse, status_code=status.HTTP_201_CREATED)
async def execute_playbook(
    execution_in: PlaybookExecutionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Start playbook execution.
    Creates a new execution instance and initiates the workflow.
    """
    # Verify playbook exists
    playbook_query = select(Playbook).where(
        Playbook.id == execution_in.playbook_id,
        Playbook.is_active == True
    )
    playbook_result = await db.execute(playbook_query)
    playbook = playbook_result.scalar_one_or_none()

    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active playbook {execution_in.playbook_id} not found"
        )

    # Verify incident if provided
    if execution_in.incident_id:
        incident_query = select(Incident).where(Incident.id == execution_in.incident_id)
        incident_result = await db.execute(incident_query)
        incident = incident_result.scalar_one_or_none()

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {execution_in.incident_id} not found"
            )

    # Create execution instance
    execution = PlaybookExecution(
        playbook_id=execution_in.playbook_id,
        incident_id=execution_in.incident_id,
        triggered_by=current_user.id,
        variables=execution_in.variables or {},
        status="pending" if playbook.approval_required else "running",
        current_step=0,
        step_results={}
    )

    # If no approval required, start immediately
    if not playbook.approval_required:
        execution.started_at = datetime.utcnow()
        execution.approved_by = current_user.id
        execution.approved_at = datetime.utcnow()

    db.add(execution)

    # Add timeline entry if incident exists
    if execution_in.incident_id:
        timeline_entry = IncidentTimeline(
            incident_id=execution_in.incident_id,
            action_type="playbook_triggered",
            actor_id=current_user.id,
            actor_type="user",
            description=f"Playbook '{playbook.name}' triggered"
        )
        db.add(timeline_entry)

    await db.commit()
    await db.refresh(execution)

    return execution


@router.post("/executions/{execution_id}/approve", response_model=PlaybookExecutionResponse)
async def approve_playbook_execution(
    execution_id: int,
    approval: PlaybookExecutionApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Approve or reject a pending playbook execution."""
    query = select(PlaybookExecution).where(PlaybookExecution.id == execution_id)
    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    if execution.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Execution is in '{execution.status}' status, cannot approve"
        )

    if approval.approve:
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        execution.approved_by = current_user.id
        execution.approved_at = datetime.utcnow()
    else:
        execution.status = "cancelled"
        execution.error_message = f"Rejected by {current_user.username}: {approval.comment or 'No reason provided'}"

    await db.commit()
    await db.refresh(execution)

    return execution


@router.patch("/executions/{execution_id}", response_model=PlaybookExecutionResponse)
async def update_playbook_execution(
    execution_id: int,
    execution_update: PlaybookExecutionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update playbook execution progress."""
    query = select(PlaybookExecution).where(PlaybookExecution.id == execution_id)
    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    update_data = execution_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(execution, field, value)

    # Set completion timestamp if status is completed or failed
    if execution.status in ["completed", "failed", "cancelled"]:
        execution.completed_at = datetime.utcnow()
        if execution.started_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.duration_seconds = int(duration)

    await db.commit()
    await db.refresh(execution)

    return execution


@router.get("/executions/{execution_id}", response_model=PlaybookExecutionResponse)
async def get_playbook_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get playbook execution details."""
    query = select(PlaybookExecution).where(PlaybookExecution.id == execution_id)
    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    return execution


@router.get("/executions/incident/{incident_id}")
async def get_incident_playbook_executions(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all playbook executions for an incident."""
    query = select(PlaybookExecution).where(
        PlaybookExecution.incident_id == incident_id
    ).order_by(PlaybookExecution.created_at.desc())

    result = await db.execute(query)
    executions = result.scalars().all()

    return {"incident_id": incident_id, "executions": executions}
