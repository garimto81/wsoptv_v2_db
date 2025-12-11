"""API Dependencies - Block E (API Agent)."""

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.catalog import (
    EpisodeService,
    EventService,
    ProjectService,
    SeasonService,
)
from ...services.hand_analysis import (
    HandClipService,
    PlayerService,
    TagService,
)
from ...services.sheets_sync import SheetsSyncService
from ...services.nas_inventory import NASFolderService, NASFileService


async def get_project_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ProjectService, None]:
    """Get project service dependency."""
    yield ProjectService(session)


async def get_season_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SeasonService, None]:
    """Get season service dependency."""
    yield SeasonService(session)


async def get_event_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[EventService, None]:
    """Get event service dependency."""
    yield EventService(session)


async def get_episode_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[EpisodeService, None]:
    """Get episode service dependency."""
    yield EpisodeService(session)


async def get_hand_clip_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[HandClipService, None]:
    """Get hand clip service dependency."""
    yield HandClipService(session)


async def get_tag_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[TagService, None]:
    """Get tag service dependency."""
    yield TagService(session)


async def get_player_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[PlayerService, None]:
    """Get player service dependency."""
    yield PlayerService(session)


async def get_sheets_sync_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SheetsSyncService, None]:
    """Get sheets sync service dependency."""
    yield SheetsSyncService(session)


async def get_nas_folder_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[NASFolderService, None]:
    """Get NAS folder service dependency."""
    yield NASFolderService(session)


async def get_nas_file_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[NASFileService, None]:
    """Get NAS file service dependency."""
    yield NASFileService(session)


# Type aliases for dependency injection
DBSessionDep = Annotated[AsyncSession, Depends(get_db)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
SeasonServiceDep = Annotated[SeasonService, Depends(get_season_service)]
EventServiceDep = Annotated[EventService, Depends(get_event_service)]
EpisodeServiceDep = Annotated[EpisodeService, Depends(get_episode_service)]
HandClipServiceDep = Annotated[HandClipService, Depends(get_hand_clip_service)]
TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
PlayerServiceDep = Annotated[PlayerService, Depends(get_player_service)]
SheetsSyncServiceDep = Annotated[SheetsSyncService, Depends(get_sheets_sync_service)]
NASFolderServiceDep = Annotated[NASFolderService, Depends(get_nas_folder_service)]
NASFileServiceDep = Annotated[NASFileService, Depends(get_nas_file_service)]
