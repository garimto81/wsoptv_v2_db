"""Player Endpoints - Block E (API Agent)."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from .deps import PlayerServiceDep
from .schemas import PlayerCreate, PlayerResponse, PlayerUpdate, PlayerWithCountResponse

router = APIRouter()


@router.get("", response_model=list[PlayerResponse])
async def list_players(
    service: PlayerServiceDep,
    nationality: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[PlayerResponse]:
    """List players, optionally filtered by nationality."""
    if nationality:
        players = await service.get_by_nationality(
            nationality, skip=skip, limit=limit
        )
    else:
        players = await service.get_all(skip=skip, limit=limit)
    return [PlayerResponse.model_validate(p) for p in players]


@router.get("/search", response_model=list[PlayerResponse])
async def search_players(
    service: PlayerServiceDep,
    q: str = Query(..., min_length=2),
    limit: int = 50,
) -> list[PlayerResponse]:
    """Search players by name."""
    players = await service.search_by_name(q, limit=limit)
    return [PlayerResponse.model_validate(p) for p in players]


@router.get("/bracelet-winners", response_model=list[PlayerResponse])
async def get_bracelet_winners(
    service: PlayerServiceDep,
    min_bracelets: int = 1,
    limit: int = 100,
) -> list[PlayerResponse]:
    """Get players with WSOP bracelets."""
    players = await service.get_bracelet_winners(
        min_bracelets=min_bracelets, limit=limit
    )
    return [PlayerResponse.model_validate(p) for p in players]


@router.get("/top-earners", response_model=list[PlayerResponse])
async def get_top_earners(
    service: PlayerServiceDep,
    limit: int = 50,
) -> list[PlayerResponse]:
    """Get players by total live earnings."""
    players = await service.get_top_earners(limit=limit)
    return [PlayerResponse.model_validate(p) for p in players]


@router.get("/frequent", response_model=list[PlayerWithCountResponse])
async def get_frequent_players(
    service: PlayerServiceDep,
    limit: int = 20,
) -> list[PlayerWithCountResponse]:
    """Get most frequently appearing players in hand clips."""
    results = await service.get_frequent_players(limit=limit)
    return [
        PlayerWithCountResponse(
            **PlayerResponse.model_validate(player).model_dump(),
            appearance_count=count,
        )
        for player, count in results
    ]


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: UUID,
    service: PlayerServiceDep,
) -> PlayerResponse:
    """Get player by ID."""
    player = await service.get_by_id(player_id)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player {player_id} not found",
        )
    return PlayerResponse.model_validate(player)


@router.post("", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(
    data: PlayerCreate,
    service: PlayerServiceDep,
) -> PlayerResponse:
    """Create a new player."""
    existing = await service.get_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Player '{data.name}' already exists",
        )
    player = await service.create_player(
        name=data.name,
        name_display=data.name_display,
        nationality=data.nationality,
        hendon_mob_id=data.hendon_mob_id,
        total_live_earnings=data.total_live_earnings,
        wsop_bracelets=data.wsop_bracelets or 0,
    )
    return PlayerResponse.model_validate(player)


@router.patch("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: UUID,
    data: PlayerUpdate,
    service: PlayerServiceDep,
) -> PlayerResponse:
    """Update a player."""
    update_data = data.model_dump(exclude_unset=True)
    player = await service.update(player_id, **update_data)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player {player_id} not found",
        )
    return PlayerResponse.model_validate(player)


@router.patch("/{player_id}/stats", response_model=PlayerResponse)
async def update_player_stats(
    player_id: UUID,
    service: PlayerServiceDep,
    total_live_earnings: Decimal | None = None,
    wsop_bracelets: int | None = None,
) -> PlayerResponse:
    """Update player statistics."""
    player = await service.update_stats(
        player_id,
        total_live_earnings=total_live_earnings,
        wsop_bracelets=wsop_bracelets,
    )
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player {player_id} not found",
        )
    return PlayerResponse.model_validate(player)


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: UUID,
    service: PlayerServiceDep,
) -> None:
    """Delete a player."""
    deleted = await service.delete(player_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player {player_id} not found",
        )
