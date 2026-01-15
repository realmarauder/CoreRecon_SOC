"""Incident API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.base import get_db
from app.models.incident import Incident, IncidentTimeline
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentResponse, IncidentListResponse

router = APIRouter()


def generate_ticket_number() -> str:
    """
    Generate unique incident ticket number.

    Format: INC-YYYY-NNNNN
    Example: INC-2026-00001
    """
    from datetime import datetime
    import random

    year = datetime.now().year
    random_num = random.randint(1, 99999)
    return f"INC-{year}-{random_num:05d}"


def calculate_sla_due_times(severity: str, created_at: datetime) -> tuple[datetime, datetime]:
    """
    Calculate SLA due times based on severity.

    Args:
        severity: Incident severity level
        created_at: Incident creation timestamp

    Returns:
        Tuple of (first_response_due, resolution_due)
    """
    from datetime import timedelta

    if severity == "critical":
        first_response = created_at + timedelta(minutes=settings.sla_critical_first_response)
        resolution = created_at + timedelta(minutes=settings.sla_critical_resolution)
    elif severity == "high":
        first_response = created_at + timedelta(minutes=settings.sla_high_first_response)
        resolution = created_at + timedelta(minutes=settings.sla_high_resolution)
    else:
        # Medium/Low/Informational - default SLA
        first_response = created_at + timedelta(hours=4)
        resolution = created_at + timedelta(hours=24)

    return first_response, resolution


@router.get("/", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_analyst_id: Optional[int] = Query(None, description="Filter by assigned analyst"),
    db: AsyncSession = Depends(get_db),
):
    """
    List incidents with pagination and filtering.

    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: 25, max: 100)
        severity: Filter by severity level
        status: Filter by incident status
        assigned_analyst_id: Filter by assigned analyst
        db: Database session

    Returns:
        Paginated list of incidents
    """
    # Build query
    query = select(Incident)

    # Apply filters
    if severity:
        query = query.where(Incident.severity == severity)
    if status:
        query = query.where(Incident.status == status)
    if assigned_analyst_id:
        query = query.where(Incident.assigned_analyst_id == assigned_analyst_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(Incident.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    incidents = result.scalars().all()

    # Calculate total pages
    pages = (total + page_size - 1) // page_size

    return IncidentListResponse(
        items=incidents,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get incident by ID.

    Args:
        incident_id: Incident database ID
        db: Database session

    Returns:
        Incident details

    Raises:
        HTTPException: 404 if incident not found
    """
    query = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found"
        )

    return incident


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new incident.

    Args:
        incident_data: Incident creation data
        db: Database session

    Returns:
        Created incident
    """
    created_at = datetime.utcnow()

    # Generate ticket number
    ticket_number = generate_ticket_number()

    # Calculate SLA due times
    first_response_due, resolution_due = calculate_sla_due_times(
        incident_data.severity,
        created_at
    )

    # Create incident
    incident = Incident(
        **incident_data.model_dump(exclude_unset=True),
        ticket_number=ticket_number,
        status="new",
        created_at=created_at,
        sla_first_response_due=first_response_due,
        sla_resolution_due=resolution_due,
        sla_breach=False
    )

    db.add(incident)
    await db.flush()  # Get the incident ID

    # Create timeline entry
    timeline_entry = IncidentTimeline(
        incident_id=incident.id,
        action_type="created",
        actor_type="system",
        description=f"Incident {ticket_number} created",
        created_at=created_at
    )
    db.add(timeline_entry)

    await db.commit()
    await db.refresh(incident)

    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    incident_update: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an incident.

    Args:
        incident_id: Incident database ID
        incident_update: Incident update data
        db: Database session

    Returns:
        Updated incident

    Raises:
        HTTPException: 404 if incident not found
    """
    query = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found"
        )

    # Track changes for timeline
    changes = {}
    update_data = incident_update.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(incident, field)
        if old_value != new_value:
            changes[field] = {"old": old_value, "new": new_value}
            setattr(incident, field, new_value)

    # Create timeline entries for significant changes
    if changes:
        for field, values in changes.items():
            timeline_entry = IncidentTimeline(
                incident_id=incident.id,
                action_type=f"updated_{field}",
                actor_type="system",
                old_value={"value": str(values["old"])},
                new_value={"value": str(values["new"])},
                description=f"Updated {field} from {values['old']} to {values['new']}",
                created_at=datetime.utcnow()
            )
            db.add(timeline_entry)

    # Check for status-specific timestamps
    if "status" in changes:
        if changes["status"]["new"] == "investigating" and not incident.first_response_at:
            incident.first_response_at = datetime.utcnow()
        elif changes["status"]["new"] == "contained" and not incident.containment_at:
            incident.containment_at = datetime.utcnow()
        elif changes["status"]["new"] in ["recovered", "closed"] and not incident.resolution_at:
            incident.resolution_at = datetime.utcnow()
        elif changes["status"]["new"] == "closed":
            incident.closed_at = datetime.utcnow()

    # Check SLA breach
    if incident.sla_first_response_due and not incident.first_response_at:
        if datetime.utcnow() > incident.sla_first_response_due:
            incident.sla_breach = True

    await db.commit()
    await db.refresh(incident)

    return incident


@router.post("/{incident_id}/assign", response_model=IncidentResponse)
async def assign_incident(
    incident_id: int,
    analyst_id: int = Query(..., description="Analyst user ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign incident to an analyst.

    Args:
        incident_id: Incident database ID
        analyst_id: Analyst user ID
        db: Database session

    Returns:
        Updated incident

    Raises:
        HTTPException: 404 if incident not found
    """
    query = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found"
        )

    old_analyst = incident.assigned_analyst_id
    incident.assigned_analyst_id = analyst_id
    incident.status = "assigned"

    # Create timeline entry
    timeline_entry = IncidentTimeline(
        incident_id=incident.id,
        action_type="assigned",
        actor_type="system",
        old_value={"analyst_id": old_analyst} if old_analyst else None,
        new_value={"analyst_id": analyst_id},
        description=f"Incident assigned to analyst {analyst_id}",
        created_at=datetime.utcnow()
    )
    db.add(timeline_entry)

    await db.commit()
    await db.refresh(incident)

    return incident


@router.post("/{incident_id}/escalate", response_model=IncidentResponse)
async def escalate_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Escalate incident severity and priority.

    Args:
        incident_id: Incident database ID
        db: Database session

    Returns:
        Updated incident

    Raises:
        HTTPException: 404 if incident not found
    """
    query = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found"
        )

    # Escalate severity
    severity_order = ["informational", "low", "medium", "high", "critical"]
    current_index = severity_order.index(incident.severity)

    if current_index < len(severity_order) - 1:
        old_severity = incident.severity
        incident.severity = severity_order[current_index + 1]

        # Recalculate SLA times
        first_response_due, resolution_due = calculate_sla_due_times(
            incident.severity,
            incident.created_at
        )
        incident.sla_first_response_due = first_response_due
        incident.sla_resolution_due = resolution_due

        # Create timeline entry
        timeline_entry = IncidentTimeline(
            incident_id=incident.id,
            action_type="escalated",
            actor_type="system",
            old_value={"severity": old_severity},
            new_value={"severity": incident.severity},
            description=f"Incident escalated from {old_severity} to {incident.severity}",
            created_at=datetime.utcnow()
        )
        db.add(timeline_entry)

        await db.commit()
        await db.refresh(incident)

    return incident


@router.get("/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get incident timeline (audit trail).

    Args:
        incident_id: Incident database ID
        db: Database session

    Returns:
        List of timeline entries

    Raises:
        HTTPException: 404 if incident not found
    """
    # Check incident exists
    incident_query = select(Incident).where(Incident.id == incident_id)
    incident_result = await db.execute(incident_query)
    incident = incident_result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found"
        )

    # Get timeline entries
    timeline_query = select(IncidentTimeline).where(
        IncidentTimeline.incident_id == incident_id
    ).order_by(IncidentTimeline.created_at.asc())

    result = await db.execute(timeline_query)
    timeline = result.scalars().all()

    return {
        "incident_id": incident_id,
        "ticket_number": incident.ticket_number,
        "timeline": timeline
    }


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an incident.

    Args:
        incident_id: Incident database ID
        db: Database session

    Raises:
        HTTPException: 404 if incident not found
    """
    query = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found"
        )

    await db.delete(incident)
    await db.commit()
