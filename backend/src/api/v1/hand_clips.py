"""HandClip Endpoints - Block E (API Agent)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from .deps import HandClipServiceDep
from .schemas import HandClipCreate, HandClipResponse, HandClipUpdate

router = APIRouter()


class AddRelationRequest(BaseModel):
    """Request to add tag or player to hand clip."""

    id: UUID


class HandClipLinkageStatsResponse(BaseModel):
    """HandClip linkage statistics."""

    total_clips: int
    with_video_file: int
    with_episode: int
    video_only: int  # Has video_file but no episode
    orphan_clips: int  # No video_file and no episode
    linkage_rate: float


@router.get("", response_model=list[HandClipResponse])
async def list_hand_clips(
    service: HandClipServiceDep,
    episode_id: UUID | None = None,
    video_file_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[HandClipResponse]:
    """List hand clips, optionally filtered."""
    if episode_id:
        clips = await service.get_by_episode(episode_id, skip=skip, limit=limit)
    elif video_file_id:
        clips = await service.get_by_video_file(video_file_id, skip=skip, limit=limit)
    else:
        clips = await service.get_all(skip=skip, limit=limit)
    return [HandClipResponse.model_validate(c) for c in clips]


@router.get("/search", response_model=list[HandClipResponse])
async def search_hand_clips(
    service: HandClipServiceDep,
    q: str = Query(..., min_length=2),
    limit: int = 50,
) -> list[HandClipResponse]:
    """Search hand clips by title."""
    clips = await service.search_by_title(q, limit=limit)
    return [HandClipResponse.model_validate(c) for c in clips]


@router.get("/by-grade/{grade}", response_model=list[HandClipResponse])
async def get_by_grade(
    grade: str,
    service: HandClipServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> list[HandClipResponse]:
    """Get hand clips by grade."""
    clips = await service.get_by_grade(grade, skip=skip, limit=limit)
    return [HandClipResponse.model_validate(c) for c in clips]


@router.get("/high-pot", response_model=list[HandClipResponse])
async def get_high_pot_clips(
    service: HandClipServiceDep,
    min_pot: int = 100000,
    limit: int = 50,
) -> list[HandClipResponse]:
    """Get hand clips with large pots."""
    clips = await service.get_high_pot_clips(min_pot=min_pot, limit=limit)
    return [HandClipResponse.model_validate(c) for c in clips]


@router.get("/by-tag/{tag_id}", response_model=list[HandClipResponse])
async def get_by_tag(
    tag_id: UUID,
    service: HandClipServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> list[HandClipResponse]:
    """Get hand clips by tag."""
    clips = await service.get_by_tag(tag_id, skip=skip, limit=limit)
    return [HandClipResponse.model_validate(c) for c in clips]


@router.get("/by-player/{player_id}", response_model=list[HandClipResponse])
async def get_by_player(
    player_id: UUID,
    service: HandClipServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> list[HandClipResponse]:
    """Get hand clips by player."""
    clips = await service.get_by_player(player_id, skip=skip, limit=limit)
    return [HandClipResponse.model_validate(c) for c in clips]


@router.get("/linkage-stats", response_model=HandClipLinkageStatsResponse)
async def get_handclip_linkage_stats(
    service: HandClipServiceDep,
) -> HandClipLinkageStatsResponse:
    """Get HandClip linkage statistics.

    Returns counts of clips by their linkage status:
    - with_video_file: Clips linked to a VideoFile
    - with_episode: Clips linked to an Episode
    - video_only: Has VideoFile but no Episode
    - orphan_clips: No VideoFile and no Episode
    """
    # Get all clips
    all_clips = await service.get_all(limit=10000)
    total = len(all_clips)

    with_video = sum(1 for c in all_clips if c.video_file_id is not None)
    with_episode = sum(1 for c in all_clips if c.episode_id is not None)
    video_only = sum(
        1 for c in all_clips
        if c.video_file_id is not None and c.episode_id is None
    )
    orphans = sum(
        1 for c in all_clips
        if c.video_file_id is None and c.episode_id is None
    )

    linkage_rate = (with_video / total * 100) if total > 0 else 0.0

    return HandClipLinkageStatsResponse(
        total_clips=total,
        with_video_file=with_video,
        with_episode=with_episode,
        video_only=video_only,
        orphan_clips=orphans,
        linkage_rate=round(linkage_rate, 1),
    )


@router.get("/{clip_id}", response_model=HandClipResponse)
async def get_hand_clip(
    clip_id: UUID,
    service: HandClipServiceDep,
) -> HandClipResponse:
    """Get hand clip by ID."""
    clip = await service.get_with_relationships(clip_id)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HandClip {clip_id} not found",
        )
    return HandClipResponse.model_validate(clip)


@router.post("", response_model=HandClipResponse, status_code=status.HTTP_201_CREATED)
async def create_hand_clip(
    data: HandClipCreate,
    service: HandClipServiceDep,
) -> HandClipResponse:
    """Create a new hand clip."""
    clip = await service.create_hand_clip(
        episode_id=data.episode_id,
        video_file_id=data.video_file_id,
        sheet_source=data.sheet_source,
        sheet_row_number=data.sheet_row_number,
        title=data.title,
        timecode=data.timecode,
        timecode_end=data.timecode_end,
        duration_seconds=data.duration_seconds,
        notes=data.notes,
        hand_grade=data.hand_grade,
        pot_size=data.pot_size,
        winner_hand=data.winner_hand,
        hands_involved=data.hands_involved,
    )
    return HandClipResponse.model_validate(clip)


@router.patch("/{clip_id}", response_model=HandClipResponse)
async def update_hand_clip(
    clip_id: UUID,
    data: HandClipUpdate,
    service: HandClipServiceDep,
) -> HandClipResponse:
    """Update a hand clip."""
    update_data = data.model_dump(exclude_unset=True)
    clip = await service.update(clip_id, **update_data)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HandClip {clip_id} not found",
        )
    return HandClipResponse.model_validate(clip)


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hand_clip(
    clip_id: UUID,
    service: HandClipServiceDep,
) -> None:
    """Delete a hand clip."""
    deleted = await service.delete(clip_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HandClip {clip_id} not found",
        )


@router.post("/{clip_id}/tags", status_code=status.HTTP_204_NO_CONTENT)
async def add_tag_to_clip(
    clip_id: UUID,
    data: AddRelationRequest,
    service: HandClipServiceDep,
) -> None:
    """Add a tag to a hand clip."""
    success = await service.add_tag(clip_id, data.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HandClip or Tag not found",
        )


@router.delete("/{clip_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_clip(
    clip_id: UUID,
    tag_id: UUID,
    service: HandClipServiceDep,
) -> None:
    """Remove a tag from a hand clip."""
    success = await service.remove_tag(clip_id, tag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HandClip or Tag not found",
        )


@router.post("/{clip_id}/players", status_code=status.HTTP_204_NO_CONTENT)
async def add_player_to_clip(
    clip_id: UUID,
    data: AddRelationRequest,
    service: HandClipServiceDep,
) -> None:
    """Add a player to a hand clip."""
    success = await service.add_player(clip_id, data.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HandClip or Player not found",
        )


@router.delete("/{clip_id}/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_player_from_clip(
    clip_id: UUID,
    player_id: UUID,
    service: HandClipServiceDep,
) -> None:
    """Remove a player from a hand clip."""
    success = await service.remove_player(clip_id, player_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HandClip or Player not found",
        )
