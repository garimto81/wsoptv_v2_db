"""Watch Progress Endpoints - User viewing progress tracking."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from .schemas import (
    WatchProgressCreate,
    WatchProgressResponse,
    ContinueWatchingItem,
)
from .auth import _get_current_user, USERS_DB

router = APIRouter()

# In-memory progress store (replace with database in production)
# Key: "{user_id}:{content_id}" -> progress data
PROGRESS_DB: dict[str, dict] = {}


def _get_progress_key(user_id: str, content_id: UUID) -> str:
    """Generate progress key."""
    return f"{user_id}:{str(content_id)}"


@router.post("", response_model=WatchProgressResponse)
async def save_progress(
    data: WatchProgressCreate,
    token: str,
) -> WatchProgressResponse:
    """Save watch progress for content."""
    user = _get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    key = _get_progress_key(user["id"], data.content_id)
    now = datetime.utcnow()

    # Calculate progress percentage
    progress_percent = 0.0
    if data.duration_seconds and data.duration_seconds > 0:
        progress_percent = min((data.position_seconds / data.duration_seconds) * 100, 100)

    # Check if completed (>= 95%)
    is_completed = progress_percent >= 95

    existing = PROGRESS_DB.get(key)
    if existing:
        # Update existing progress
        existing["position_seconds"] = data.position_seconds
        existing["duration_seconds"] = data.duration_seconds
        existing["progress_percent"] = progress_percent
        existing["is_completed"] = is_completed
        existing["updated_at"] = now.isoformat()
        progress_data = existing
    else:
        # Create new progress
        progress_data = {
            "user_id": user["id"],
            "content_id": str(data.content_id),
            "position_seconds": data.position_seconds,
            "duration_seconds": data.duration_seconds,
            "progress_percent": progress_percent,
            "is_completed": is_completed,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        PROGRESS_DB[key] = progress_data

    return WatchProgressResponse(
        user_id=UUID(progress_data["user_id"]),
        content_id=UUID(progress_data["content_id"]),
        position_seconds=progress_data["position_seconds"],
        duration_seconds=progress_data["duration_seconds"],
        progress_percent=progress_data["progress_percent"],
        is_completed=progress_data["is_completed"],
        updated_at=datetime.fromisoformat(progress_data["updated_at"]),
    )


@router.get("/{content_id}", response_model=WatchProgressResponse | None)
async def get_progress(
    content_id: UUID,
    token: str,
) -> WatchProgressResponse | None:
    """Get watch progress for specific content."""
    user = _get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    key = _get_progress_key(user["id"], content_id)
    progress_data = PROGRESS_DB.get(key)

    if not progress_data:
        return None

    return WatchProgressResponse(
        user_id=UUID(progress_data["user_id"]),
        content_id=UUID(progress_data["content_id"]),
        position_seconds=progress_data["position_seconds"],
        duration_seconds=progress_data["duration_seconds"],
        progress_percent=progress_data["progress_percent"],
        is_completed=progress_data["is_completed"],
        updated_at=datetime.fromisoformat(progress_data["updated_at"]),
    )


@router.get("", response_model=list[WatchProgressResponse])
async def get_all_progress(
    token: str,
    limit: int = 20,
) -> list[WatchProgressResponse]:
    """Get all watch progress for current user."""
    user = _get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_prefix = f"{user['id']}:"
    user_progress = []

    for key, data in PROGRESS_DB.items():
        if key.startswith(user_prefix):
            user_progress.append(
                WatchProgressResponse(
                    user_id=UUID(data["user_id"]),
                    content_id=UUID(data["content_id"]),
                    position_seconds=data["position_seconds"],
                    duration_seconds=data["duration_seconds"],
                    progress_percent=data["progress_percent"],
                    is_completed=data["is_completed"],
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                )
            )

    # Sort by updated_at descending and limit
    user_progress.sort(key=lambda x: x.updated_at, reverse=True)
    return user_progress[:limit]


@router.delete("/{content_id}")
async def delete_progress(
    content_id: UUID,
    token: str,
) -> dict:
    """Delete watch progress for specific content."""
    user = _get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    key = _get_progress_key(user["id"], content_id)
    if key in PROGRESS_DB:
        del PROGRESS_DB[key]

    return {"message": "Progress deleted successfully"}


@router.post("/{content_id}/complete")
async def mark_completed(
    content_id: UUID,
    token: str,
) -> WatchProgressResponse:
    """Mark content as completed."""
    user = _get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    key = _get_progress_key(user["id"], content_id)
    now = datetime.utcnow()

    existing = PROGRESS_DB.get(key)
    if existing:
        existing["is_completed"] = True
        existing["progress_percent"] = 100
        existing["updated_at"] = now.isoformat()
        progress_data = existing
    else:
        # Create completed progress
        progress_data = {
            "user_id": user["id"],
            "content_id": str(content_id),
            "position_seconds": 0,
            "duration_seconds": 0,
            "progress_percent": 100,
            "is_completed": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        PROGRESS_DB[key] = progress_data

    return WatchProgressResponse(
        user_id=UUID(progress_data["user_id"]),
        content_id=UUID(progress_data["content_id"]),
        position_seconds=progress_data["position_seconds"],
        duration_seconds=progress_data["duration_seconds"],
        progress_percent=progress_data["progress_percent"],
        is_completed=progress_data["is_completed"],
        updated_at=datetime.fromisoformat(progress_data["updated_at"]),
    )
