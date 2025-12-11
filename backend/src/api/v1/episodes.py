"""Episode Endpoints - Block E (API Agent)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from .deps import EpisodeServiceDep
from .schemas import EpisodeCreate, EpisodeResponse, EpisodeUpdate

router = APIRouter()


@router.get("", response_model=list[EpisodeResponse])
async def list_episodes(
    service: EpisodeServiceDep,
    event_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[EpisodeResponse]:
    """List episodes, optionally filtered by event."""
    if event_id:
        episodes = await service.get_by_event(event_id, skip=skip, limit=limit)
    else:
        episodes = await service.get_all(skip=skip, limit=limit)
    return [EpisodeResponse.model_validate(e) for e in episodes]


@router.get("/search", response_model=list[EpisodeResponse])
async def search_episodes(
    service: EpisodeServiceDep,
    q: str = Query(..., min_length=2),
    event_id: UUID | None = None,
    limit: int = 50,
) -> list[EpisodeResponse]:
    """Search episodes by title."""
    episodes = await service.search_by_title(q, event_id=event_id, limit=limit)
    return [EpisodeResponse.model_validate(e) for e in episodes]


@router.get("/final-tables", response_model=list[EpisodeResponse])
async def get_final_tables(
    service: EpisodeServiceDep,
    event_id: UUID,
) -> list[EpisodeResponse]:
    """Get final table episodes for an event."""
    episodes = await service.get_final_tables(event_id)
    return [EpisodeResponse.model_validate(e) for e in episodes]


@router.get("/duration/{event_id}", response_model=dict)
async def get_total_duration(
    event_id: UUID,
    service: EpisodeServiceDep,
) -> dict:
    """Get total duration of all episodes for an event."""
    total_seconds = await service.get_total_duration(event_id)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return {
        "event_id": str(event_id),
        "total_seconds": total_seconds,
        "formatted": f"{hours}h {minutes}m {seconds}s",
    }


@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: UUID,
    service: EpisodeServiceDep,
) -> EpisodeResponse:
    """Get episode by ID."""
    episode = await service.get_by_id(episode_id)
    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {episode_id} not found",
        )
    return EpisodeResponse.model_validate(episode)


@router.post("", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
async def create_episode(
    data: EpisodeCreate,
    service: EpisodeServiceDep,
) -> EpisodeResponse:
    """Create a new episode."""
    episode = await service.create_episode(
        event_id=data.event_id,
        episode_number=data.episode_number,
        day_number=data.day_number,
        part_number=data.part_number,
        title=data.title,
        episode_type=data.episode_type,
        table_type=data.table_type,
        duration_seconds=data.duration_seconds,
    )
    return EpisodeResponse.model_validate(episode)


@router.patch("/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: UUID,
    data: EpisodeUpdate,
    service: EpisodeServiceDep,
) -> EpisodeResponse:
    """Update an episode."""
    update_data = data.model_dump(exclude_unset=True)
    episode = await service.update(episode_id, **update_data)
    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {episode_id} not found",
        )
    return EpisodeResponse.model_validate(episode)


@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: UUID,
    service: EpisodeServiceDep,
) -> None:
    """Delete an episode."""
    deleted = await service.delete(episode_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {episode_id} not found",
        )
