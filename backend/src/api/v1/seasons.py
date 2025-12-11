"""Season Endpoints - Block E (API Agent)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from .deps import SeasonServiceDep
from .schemas import SeasonCreate, SeasonResponse, SeasonUpdate

router = APIRouter()


@router.get("", response_model=list[SeasonResponse])
async def list_seasons(
    service: SeasonServiceDep,
    project_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[SeasonResponse]:
    """List seasons, optionally filtered by project."""
    if project_id:
        seasons = await service.get_by_project(project_id, skip=skip, limit=limit)
    else:
        seasons = await service.get_all(skip=skip, limit=limit)
    return [SeasonResponse.model_validate(s) for s in seasons]


@router.get("/{season_id}", response_model=SeasonResponse)
async def get_season(
    season_id: UUID,
    service: SeasonServiceDep,
) -> SeasonResponse:
    """Get season by ID."""
    season = await service.get_by_id(season_id)
    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Season {season_id} not found",
        )
    return SeasonResponse.model_validate(season)


@router.get("/project/{project_id}/years", response_model=list[int])
async def get_years_for_project(
    project_id: UUID,
    service: SeasonServiceDep,
) -> list[int]:
    """Get distinct years for a project."""
    return await service.get_years_for_project(project_id)


@router.post("", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
async def create_season(
    data: SeasonCreate,
    service: SeasonServiceDep,
) -> SeasonResponse:
    """Create a new season."""
    existing = await service.get_by_project_and_year(
        data.project_id, data.year, data.sub_category
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Season for year {data.year} already exists",
        )
    season = await service.create_season(
        project_id=data.project_id,
        year=data.year,
        name=data.name,
        location=data.location,
        sub_category=data.sub_category,
    )
    return SeasonResponse.model_validate(season)


@router.patch("/{season_id}", response_model=SeasonResponse)
async def update_season(
    season_id: UUID,
    data: SeasonUpdate,
    service: SeasonServiceDep,
) -> SeasonResponse:
    """Update a season."""
    update_data = data.model_dump(exclude_unset=True)
    season = await service.update(season_id, **update_data)
    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Season {season_id} not found",
        )
    return SeasonResponse.model_validate(season)


@router.delete("/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_season(
    season_id: UUID,
    service: SeasonServiceDep,
) -> None:
    """Delete a season."""
    deleted = await service.delete(season_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Season {season_id} not found",
        )
