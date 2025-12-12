"""Contents Endpoints - Netflix-style content browsing."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Query

from .deps import (
    CatalogItemServiceDep,
    ProjectServiceDep,
    SeasonServiceDep,
    EventServiceDep,
    EpisodeServiceDep,
)
from .schemas import (
    CatalogItemResponse,
    CatalogBrowseResponse,
    ContentItem,
    FeaturedContent,
    ContentRow,
    BrowseResponse,
    Top10Item,
    ContinueWatchingItem,
)
from .auth import _get_current_user
from .progress import PROGRESS_DB

router = APIRouter()


def _episode_to_content_item(
    episode,
    event,
    season,
    project,
    progress: Optional[float] = None,
) -> ContentItem:
    """Convert episode to content item."""
    title = episode.title or f"{project.name} {season.year} - Episode {episode.episode_number or 1}"
    if event.name_short:
        title = f"{event.name_short} - {title}"

    return ContentItem(
        id=episode.id,
        title=title,
        description=f"{event.name} - {episode.episode_type or 'Episode'}",
        thumbnail_url=None,  # TODO: Add thumbnail support
        backdrop_url=None,
        category=project.code,
        year=season.year,
        duration_seconds=episode.duration_seconds,
        quality="HD",
        tags=[project.name, str(season.year), event.name],
        progress=progress,
    )


@router.get("/browse", response_model=BrowseResponse)
async def get_browse_page(
    project_service: ProjectServiceDep,
    season_service: SeasonServiceDep,
    event_service: EventServiceDep,
    episode_service: EpisodeServiceDep,
    category: Optional[str] = None,
) -> BrowseResponse:
    """Get Netflix-style browse page with featured content and rows."""
    rows = []

    # Get all active projects
    projects = await project_service.get_all(limit=100)
    project_map = {p.id: p for p in projects}

    # Filter by category if specified
    if category:
        projects = [p for p in projects if p.code.lower() == category.lower()]

    # Featured content (latest episode from first project)
    featured = None
    for project in projects[:1]:
        seasons = await season_service.get_by_project(project.id, limit=1)
        if seasons:
            events = await event_service.get_by_season(seasons[0].id, limit=1)
            if events:
                episodes = await episode_service.get_by_event(events[0].id, limit=1)
                if episodes:
                    featured = FeaturedContent(
                        id=episodes[0].id,
                        title=f"{project.name} {seasons[0].year} Main Event Final Table",
                        description=f"Experience the thrilling conclusion of {project.name} {seasons[0].year}. "
                                    f"Watch as top players battle for the championship.",
                        category=project.code,
                        year=seasons[0].year,
                        duration_seconds=episodes[0].duration_seconds,
                        quality="HD",
                        tags=[project.name, "Final Table", "Main Event"],
                        players=["Phil Ivey", "Daniel Negreanu"],  # TODO: Get from hand_clips
                        event_type=events[0].event_type or "Tournament",
                    )

    # Continue Watching row (mock data for now)
    continue_watching = ContentRow(
        title="Continue Watching",
        row_type="continue-watching",
        items=[],  # TODO: Integrate with user watch progress
    )
    rows.append(continue_watching)

    # Top 10 row
    top10_items = []
    all_episodes = []
    for project in projects[:3]:
        seasons = await season_service.get_by_project(project.id, limit=2)
        for season in seasons:
            events = await event_service.get_by_season(season.id, limit=3)
            for event in events:
                episodes = await episode_service.get_by_event(event.id, limit=2)
                for ep in episodes:
                    all_episodes.append((ep, event, season, project))

    for idx, (ep, ev, se, pr) in enumerate(all_episodes[:10]):
        item = _episode_to_content_item(ep, ev, se, pr)
        top10_items.append(
            Top10Item(
                **item.model_dump(),
                rank=idx + 1,
            )
        )

    if top10_items:
        rows.append(
            ContentRow(
                title="Today in WSOPTV",
                row_type="top10",
                items=top10_items,
            )
        )

    # Project-specific rows
    for project in projects:
        seasons = await season_service.get_by_project(project.id, limit=3)
        items = []
        for season in seasons:
            events = await event_service.get_by_season(season.id, limit=5)
            for event in events:
                episodes = await episode_service.get_by_event(event.id, limit=3)
                for ep in episodes:
                    items.append(_episode_to_content_item(ep, event, season, project))

        if items:
            rows.append(
                ContentRow(
                    title=f"{project.name} Series",
                    row_type="default",
                    items=items[:12],  # Max 12 items per row
                )
            )

    return BrowseResponse(
        featured=featured,
        rows=rows,
    )


@router.get("/featured", response_model=FeaturedContent | None)
async def get_featured_content(
    project_service: ProjectServiceDep,
    season_service: SeasonServiceDep,
    event_service: EventServiceDep,
    episode_service: EpisodeServiceDep,
) -> FeaturedContent | None:
    """Get featured content for hero billboard."""
    projects = await project_service.get_all(limit=1)
    if not projects:
        return None

    project = projects[0]
    seasons = await season_service.get_by_project(project.id, limit=1)
    if not seasons:
        return None

    events = await event_service.get_by_season(seasons[0].id, limit=1)
    if not events:
        return None

    episodes = await episode_service.get_by_event(events[0].id, limit=1)
    if not episodes:
        return None

    return FeaturedContent(
        id=episodes[0].id,
        title=f"{project.name} {seasons[0].year} Main Event",
        description=f"The most exciting moments from {project.name} {seasons[0].year}.",
        category=project.code,
        year=seasons[0].year,
        duration_seconds=episodes[0].duration_seconds,
        quality="HD",
        tags=[project.name, "Main Event"],
        players=[],
        event_type=events[0].event_type,
    )


@router.get("/top10", response_model=list[Top10Item])
async def get_top10(
    project_service: ProjectServiceDep,
    season_service: SeasonServiceDep,
    event_service: EventServiceDep,
    episode_service: EpisodeServiceDep,
) -> list[Top10Item]:
    """Get top 10 trending content."""
    items = []
    projects = await project_service.get_all(limit=5)

    for project in projects:
        seasons = await season_service.get_by_project(project.id, limit=2)
        for season in seasons:
            events = await event_service.get_by_season(season.id, limit=2)
            for event in events:
                episodes = await episode_service.get_by_event(event.id, limit=1)
                for ep in episodes:
                    item = _episode_to_content_item(ep, event, season, project)
                    items.append(item)

    return [
        Top10Item(**item.model_dump(), rank=idx + 1)
        for idx, item in enumerate(items[:10])
    ]


@router.get("/continue", response_model=list[ContinueWatchingItem])
async def get_continue_watching(
    token: str,
    project_service: ProjectServiceDep,
    season_service: SeasonServiceDep,
    event_service: EventServiceDep,
    episode_service: EpisodeServiceDep,
    limit: int = 10,
) -> list[ContinueWatchingItem]:
    """Get continue watching list for current user."""
    user = _get_current_user(token)
    if not user:
        return []

    user_prefix = f"{user['id']}:"
    continue_items = []

    for key, progress in PROGRESS_DB.items():
        if not key.startswith(user_prefix):
            continue
        if progress.get("is_completed", False):
            continue
        if progress.get("progress_percent", 0) < 5:
            continue

        content_id = UUID(progress["content_id"])
        episode = await episode_service.get_by_id(content_id)
        if not episode:
            continue

        event = await event_service.get_by_id(episode.event_id)
        if not event:
            continue

        season = await season_service.get_by_id(event.season_id)
        if not season:
            continue

        project = await project_service.get_by_id(season.project_id)
        if not project:
            continue

        base_item = _episode_to_content_item(
            episode, event, season, project, progress.get("progress_percent")
        )
        continue_items.append(
            ContinueWatchingItem(
                **base_item.model_dump(),
                position_seconds=progress["position_seconds"],
                last_watched=datetime.fromisoformat(progress["updated_at"]),
            )
        )

    # Sort by last watched descending
    continue_items.sort(key=lambda x: x.last_watched, reverse=True)
    return continue_items[:limit]


@router.get("/category/{category}", response_model=list[ContentItem])
async def get_by_category(
    category: str,
    project_service: ProjectServiceDep,
    season_service: SeasonServiceDep,
    event_service: EventServiceDep,
    episode_service: EpisodeServiceDep,
    limit: int = 20,
) -> list[ContentItem]:
    """Get content by category."""
    items = []

    # Find project by code
    projects = await project_service.get_all(limit=100)
    project = next((p for p in projects if p.code.lower() == category.lower()), None)

    if not project:
        return []

    seasons = await season_service.get_by_project(project.id, limit=5)
    for season in seasons:
        events = await event_service.get_by_season(season.id, limit=10)
        for event in events:
            episodes = await episode_service.get_by_event(event.id, limit=5)
            for ep in episodes:
                items.append(_episode_to_content_item(ep, event, season, project))
                if len(items) >= limit:
                    return items

    return items


@router.get("/{content_id}", response_model=ContentItem | None)
async def get_content(
    content_id: UUID,
    project_service: ProjectServiceDep,
    season_service: SeasonServiceDep,
    event_service: EventServiceDep,
    episode_service: EpisodeServiceDep,
) -> ContentItem | None:
    """Get single content item by ID."""
    episode = await episode_service.get_by_id(content_id)
    if not episode:
        return None

    event = await event_service.get_by_id(episode.event_id)
    if not event:
        return None

    season = await season_service.get_by_id(event.season_id)
    if not season:
        return None

    project = await project_service.get_by_id(season.project_id)
    if not project:
        return None

    return _episode_to_content_item(episode, event, season, project)


# ==================== CatalogItem-based Endpoints ====================


@router.get("/v2/browse", response_model=list[CatalogItemResponse])
async def get_catalog_browse(
    catalog_service: CatalogItemServiceDep,
    project_code: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[CatalogItemResponse]:
    """Netflix-style browse using CatalogItem (optimized)."""
    items = await catalog_service.get_browse_items(
        project_code=project_code,
        category=category,
        year=year,
        skip=skip,
        limit=limit,
    )
    return [CatalogItemResponse.model_validate(item) for item in items]


@router.get("/v2/featured", response_model=list[CatalogItemResponse])
async def get_catalog_featured(
    catalog_service: CatalogItemServiceDep,
    limit: int = 5,
) -> list[CatalogItemResponse]:
    """Get featured content from CatalogItem."""
    items = await catalog_service.get_featured_items(limit=limit)
    return [CatalogItemResponse.model_validate(item) for item in items]


@router.get("/v2/top10", response_model=list[CatalogItemResponse])
async def get_catalog_top10(
    catalog_service: CatalogItemServiceDep,
    project_code: Optional[str] = None,
) -> list[CatalogItemResponse]:
    """Get Top 10 from CatalogItem."""
    items = await catalog_service.get_top10_items(project_code=project_code)
    return [CatalogItemResponse.model_validate(item) for item in items]


@router.get("/v2/project/{project_code}", response_model=list[CatalogItemResponse])
async def get_catalog_by_project(
    project_code: str,
    catalog_service: CatalogItemServiceDep,
    skip: int = 0,
    limit: int = 50,
) -> list[CatalogItemResponse]:
    """Get catalog items by project code."""
    items = await catalog_service.get_by_project(
        project_code=project_code.upper(),
        skip=skip,
        limit=limit,
    )
    return [CatalogItemResponse.model_validate(item) for item in items]


@router.get("/v2/{catalog_id}", response_model=CatalogItemResponse | None)
async def get_catalog_item(
    catalog_id: UUID,
    catalog_service: CatalogItemServiceDep,
) -> CatalogItemResponse | None:
    """Get single catalog item by ID."""
    item = await catalog_service.get_by_id(catalog_id)
    if not item:
        return None
    return CatalogItemResponse.model_validate(item)
