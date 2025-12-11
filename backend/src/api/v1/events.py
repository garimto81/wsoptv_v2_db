"""Event Endpoints - Block E (API Agent)."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from .deps import EventServiceDep
from .schemas import EventCreate, EventResponse, EventUpdate

router = APIRouter()


@router.get("", response_model=list[EventResponse])
async def list_events(
    service: EventServiceDep,
    season_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[EventResponse]:
    """List events, optionally filtered by season."""
    if season_id:
        events = await service.get_by_season(season_id, skip=skip, limit=limit)
    else:
        events = await service.get_all(skip=skip, limit=limit)
    return [EventResponse.model_validate(e) for e in events]


@router.get("/search", response_model=list[EventResponse])
async def search_events(
    service: EventServiceDep,
    q: str = Query(..., min_length=2),
    season_id: UUID | None = None,
    limit: int = 50,
) -> list[EventResponse]:
    """Search events by name."""
    events = await service.search_by_name(q, season_id=season_id, limit=limit)
    return [EventResponse.model_validate(e) for e in events]


@router.get("/high-roller", response_model=list[EventResponse])
async def get_high_roller_events(
    service: EventServiceDep,
    season_id: UUID,
    min_buy_in: Decimal = Decimal("10000"),
) -> list[EventResponse]:
    """Get high roller events."""
    events = await service.get_high_roller_events(season_id, min_buy_in)
    return [EventResponse.model_validate(e) for e in events]


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    service: EventServiceDep,
) -> EventResponse:
    """Get event by ID."""
    event = await service.get_by_id(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )
    return EventResponse.model_validate(event)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    service: EventServiceDep,
) -> EventResponse:
    """Create a new event."""
    if data.event_number:
        existing = await service.get_by_season_and_number(
            data.season_id, data.event_number
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Event #{data.event_number} already exists in this season",
            )
    event = await service.create_event(
        season_id=data.season_id,
        name=data.name,
        event_number=data.event_number,
        name_short=data.name_short,
        event_type=data.event_type,
        game_type=data.game_type,
        buy_in=data.buy_in,
        gtd_amount=data.gtd_amount,
        venue=data.venue,
    )
    return EventResponse.model_validate(event)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    data: EventUpdate,
    service: EventServiceDep,
) -> EventResponse:
    """Update an event."""
    update_data = data.model_dump(exclude_unset=True)
    event = await service.update(event_id, **update_data)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )
    return EventResponse.model_validate(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    service: EventServiceDep,
) -> None:
    """Delete an event."""
    deleted = await service.delete(event_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )
