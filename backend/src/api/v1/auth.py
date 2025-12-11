"""Auth Endpoints - User authentication and management."""

import hashlib
import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from .schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserStatusUpdate,
    TokenResponse,
)

router = APIRouter()

# In-memory user store (replace with database in production)
USERS_DB: dict[str, dict] = {}
TOKENS_DB: dict[str, str] = {}  # token -> user_id

# Default admin account
DEFAULT_ADMIN = {
    "id": str(uuid4()),
    "username": "garimto",
    "password_hash": hashlib.sha256("1234".encode()).hexdigest(),
    "role": "admin",
    "status": "active",
    "created_at": datetime.utcnow().isoformat(),
    "approved_at": datetime.utcnow().isoformat(),
    "approved_by": None,
}


def _init_db():
    """Initialize default admin if not exists."""
    if "garimto" not in USERS_DB:
        USERS_DB["garimto"] = DEFAULT_ADMIN


def _hash_password(password: str) -> str:
    """Hash password with SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return _hash_password(password) == password_hash


def _generate_token() -> str:
    """Generate secure token."""
    return secrets.token_urlsafe(32)


def _get_current_user(token: str) -> Optional[dict]:
    """Get current user from token."""
    user_id = TOKENS_DB.get(token)
    if not user_id:
        return None
    for user in USERS_DB.values():
        if user["id"] == user_id:
            return user
    return None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate) -> UserResponse:
    """Register a new user (pending approval)."""
    _init_db()

    # Check if username exists
    if data.username.lower() in [u.lower() for u in USERS_DB.keys()]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Validate username
    if len(data.username) < 4 or len(data.username) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 4-20 characters",
        )

    # Create user
    user_id = str(uuid4())
    user = {
        "id": user_id,
        "username": data.username,
        "password_hash": _hash_password(data.password),
        "role": "user",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "approved_at": None,
        "approved_by": None,
    }
    USERS_DB[data.username] = user

    return UserResponse(
        id=UUID(user_id),
        username=data.username,
        role="user",
        status="pending",
        created_at=datetime.fromisoformat(user["created_at"]),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin) -> TokenResponse:
    """Login and get access token."""
    _init_db()

    # Find user
    user = USERS_DB.get(data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not _verify_password(data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check status
    if user["status"] == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval",
        )
    if user["status"] == "rejected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been rejected",
        )
    if user["status"] == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended",
        )

    # Generate token
    token = _generate_token()
    TOKENS_DB[token] = user["id"]

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=UUID(user["id"]),
            username=user["username"],
            role=user["role"],
            status=user["status"],
            created_at=datetime.fromisoformat(user["created_at"]),
            approved_at=datetime.fromisoformat(user["approved_at"]) if user["approved_at"] else None,
        ),
    )


@router.post("/logout")
async def logout(token: str) -> dict:
    """Logout and invalidate token."""
    if token in TOKENS_DB:
        del TOKENS_DB[token]
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str) -> UserResponse:
    """Get current user info."""
    user = _get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return UserResponse(
        id=UUID(user["id"]),
        username=user["username"],
        role=user["role"],
        status=user["status"],
        created_at=datetime.fromisoformat(user["created_at"]),
        approved_at=datetime.fromisoformat(user["approved_at"]) if user["approved_at"] else None,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    token: str,
    status_filter: Optional[str] = None,
) -> list[UserResponse]:
    """List all users (admin only)."""
    _init_db()

    user = _get_current_user(token)
    if not user or user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    users = []
    for u in USERS_DB.values():
        if status_filter and u["status"] != status_filter:
            continue
        users.append(
            UserResponse(
                id=UUID(u["id"]),
                username=u["username"],
                role=u["role"],
                status=u["status"],
                created_at=datetime.fromisoformat(u["created_at"]),
                approved_at=datetime.fromisoformat(u["approved_at"]) if u["approved_at"] else None,
            )
        )

    return users


@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: UUID,
    data: UserStatusUpdate,
    token: str,
) -> UserResponse:
    """Update user status (admin only)."""
    _init_db()

    admin = _get_current_user(token)
    if not admin or admin["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Find user
    target_user = None
    for u in USERS_DB.values():
        if u["id"] == str(user_id):
            target_user = u
            break

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate status
    valid_statuses = ["pending", "active", "rejected", "suspended"]
    if data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    # Update status
    target_user["status"] = data.status
    if data.status == "active" and not target_user["approved_at"]:
        target_user["approved_at"] = datetime.utcnow().isoformat()
        target_user["approved_by"] = admin["id"]

    return UserResponse(
        id=UUID(target_user["id"]),
        username=target_user["username"],
        role=target_user["role"],
        status=target_user["status"],
        created_at=datetime.fromisoformat(target_user["created_at"]),
        approved_at=datetime.fromisoformat(target_user["approved_at"]) if target_user["approved_at"] else None,
        approved_by=UUID(target_user["approved_by"]) if target_user["approved_by"] else None,
    )
