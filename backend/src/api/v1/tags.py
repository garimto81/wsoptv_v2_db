"""Tag Endpoints - Block E (API Agent)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from .deps import TagServiceDep
from .schemas import TagCreate, TagResponse, TagUpdate, TagWithCountResponse

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    service: TagServiceDep,
    category: str | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[TagResponse]:
    """List tags, optionally filtered by category."""
    if category:
        tags = await service.get_by_category(category, active_only=active_only)
    else:
        tags = await service.get_all(skip=skip, limit=limit)
    return [TagResponse.model_validate(t) for t in tags]


@router.get("/search", response_model=list[TagResponse])
async def search_tags(
    service: TagServiceDep,
    q: str = Query(..., min_length=1),
    category: str | None = None,
    limit: int = 50,
) -> list[TagResponse]:
    """Search tags by name."""
    tags = await service.search_by_name(q, category=category, limit=limit)
    return [TagResponse.model_validate(t) for t in tags]


@router.get("/popular", response_model=list[TagWithCountResponse])
async def get_popular_tags(
    service: TagServiceDep,
    category: str | None = None,
    limit: int = 20,
) -> list[TagWithCountResponse]:
    """Get most used tags."""
    results = await service.get_popular_tags(category=category, limit=limit)
    return [
        TagWithCountResponse(
            **TagResponse.model_validate(tag).model_dump(),
            usage_count=count,
        )
        for tag, count in results
    ]


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: UUID,
    service: TagServiceDep,
) -> TagResponse:
    """Get tag by ID."""
    tag = await service.get_by_id(tag_id)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found",
        )
    return TagResponse.model_validate(tag)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    service: TagServiceDep,
) -> TagResponse:
    """Create a new tag."""
    existing = await service.get_by_category_and_name(data.category, data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag '{data.name}' already exists in category '{data.category}'",
        )
    tag = await service.create_tag(
        category=data.category,
        name=data.name,
        name_display=data.name_display,
        description=data.description,
        sort_order=data.sort_order,
    )
    return TagResponse.model_validate(tag)


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    service: TagServiceDep,
) -> TagResponse:
    """Update a tag."""
    update_data = data.model_dump(exclude_unset=True)
    tag = await service.update(tag_id, **update_data)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found",
        )
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    service: TagServiceDep,
) -> None:
    """Delete a tag."""
    deleted = await service.delete(tag_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found",
        )


@router.post("/seed", response_model=list[TagResponse])
async def seed_default_tags(
    service: TagServiceDep,
) -> list[TagResponse]:
    """Seed default tags."""
    tags = await service.seed_default_tags()
    return [TagResponse.model_validate(t) for t in tags]
