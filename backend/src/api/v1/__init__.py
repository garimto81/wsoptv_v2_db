"""API v1 Module - Block E (API Agent)."""

from fastapi import APIRouter

from .projects import router as projects_router
from .seasons import router as seasons_router
from .events import router as events_router
from .episodes import router as episodes_router
from .hand_clips import router as hand_clips_router
from .tags import router as tags_router
from .players import router as players_router
from .sync import router as sync_router
from .health import router as health_router
from .nas import router as nas_router
from .quality import router as quality_router
from .auth import router as auth_router
from .contents import router as contents_router
from .progress import router as progress_router

api_router = APIRouter()

# Health check
api_router.include_router(health_router, tags=["health"])

# Authentication
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# Netflix-style Contents API
api_router.include_router(contents_router, prefix="/contents", tags=["contents"])

# Watch Progress API
api_router.include_router(progress_router, prefix="/progress", tags=["progress"])

# Block B - Catalog
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(seasons_router, prefix="/seasons", tags=["seasons"])
api_router.include_router(events_router, prefix="/events", tags=["events"])
api_router.include_router(episodes_router, prefix="/episodes", tags=["episodes"])

# Block C - Hand Analysis
api_router.include_router(hand_clips_router, prefix="/hand-clips", tags=["hand-clips"])
api_router.include_router(tags_router, prefix="/tags", tags=["tags"])
api_router.include_router(players_router, prefix="/players", tags=["players"])

# Block D - Sheets Sync
api_router.include_router(sync_router, prefix="/sync", tags=["sync"])

# Block A - NAS Inventory
api_router.include_router(nas_router)

# Data Quality Dashboard
api_router.include_router(quality_router)

__all__ = ["api_router"]
