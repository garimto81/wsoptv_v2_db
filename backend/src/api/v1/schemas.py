"""API Schemas - Block E (API Agent).

Pydantic schemas for request/response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common config."""

    model_config = ConfigDict(from_attributes=True)


# Project schemas
class ProjectBase(BaseModel):
    """Project base schema."""

    code: str
    name: str
    description: Optional[str] = None
    nas_base_path: Optional[str] = None
    filename_pattern: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Project create schema."""

    pass


class ProjectUpdate(BaseModel):
    """Project update schema."""

    name: Optional[str] = None
    description: Optional[str] = None
    nas_base_path: Optional[str] = None
    filename_pattern: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase, BaseSchema):
    """Project response schema."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Season schemas
class SeasonBase(BaseModel):
    """Season base schema."""

    year: int
    name: str
    location: Optional[str] = None
    sub_category: Optional[str] = None


class SeasonCreate(SeasonBase):
    """Season create schema."""

    project_id: UUID


class SeasonUpdate(BaseModel):
    """Season update schema."""

    name: Optional[str] = None
    location: Optional[str] = None
    sub_category: Optional[str] = None
    status: Optional[str] = None


class SeasonResponse(SeasonBase, BaseSchema):
    """Season response schema."""

    id: UUID
    project_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


# Event schemas
class EventBase(BaseModel):
    """Event base schema."""

    name: str
    event_number: Optional[int] = None
    name_short: Optional[str] = None
    event_type: Optional[str] = None
    game_type: Optional[str] = None
    buy_in: Optional[Decimal] = None
    gtd_amount: Optional[Decimal] = None
    venue: Optional[str] = None


class EventCreate(EventBase):
    """Event create schema."""

    season_id: UUID


class EventUpdate(BaseModel):
    """Event update schema."""

    name: Optional[str] = None
    event_number: Optional[int] = None
    name_short: Optional[str] = None
    event_type: Optional[str] = None
    game_type: Optional[str] = None
    buy_in: Optional[Decimal] = None
    gtd_amount: Optional[Decimal] = None
    venue: Optional[str] = None
    status: Optional[str] = None


class EventResponse(EventBase, BaseSchema):
    """Event response schema."""

    id: UUID
    season_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


# Episode schemas
class EpisodeBase(BaseModel):
    """Episode base schema."""

    episode_number: Optional[int] = None
    day_number: Optional[int] = None
    part_number: Optional[int] = None
    title: Optional[str] = None
    episode_type: Optional[str] = None
    table_type: Optional[str] = None
    duration_seconds: Optional[int] = None


class EpisodeCreate(EpisodeBase):
    """Episode create schema."""

    event_id: UUID


class EpisodeUpdate(BaseModel):
    """Episode update schema."""

    episode_number: Optional[int] = None
    day_number: Optional[int] = None
    part_number: Optional[int] = None
    title: Optional[str] = None
    episode_type: Optional[str] = None
    table_type: Optional[str] = None
    duration_seconds: Optional[int] = None


class EpisodeResponse(EpisodeBase, BaseSchema):
    """Episode response schema."""

    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime


# HandClip schemas
class HandClipBase(BaseModel):
    """HandClip base schema."""

    title: Optional[str] = None
    timecode: Optional[str] = None
    timecode_end: Optional[str] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    hand_grade: Optional[str] = None
    pot_size: Optional[int] = None
    winner_hand: Optional[str] = None
    hands_involved: Optional[str] = None


class HandClipCreate(HandClipBase):
    """HandClip create schema."""

    episode_id: Optional[UUID] = None
    video_file_id: Optional[UUID] = None
    sheet_source: Optional[str] = None
    sheet_row_number: Optional[int] = None


class HandClipUpdate(BaseModel):
    """HandClip update schema."""

    title: Optional[str] = None
    timecode: Optional[str] = None
    timecode_end: Optional[str] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    hand_grade: Optional[str] = None
    pot_size: Optional[int] = None
    winner_hand: Optional[str] = None
    hands_involved: Optional[str] = None


class HandClipResponse(HandClipBase, BaseSchema):
    """HandClip response schema."""

    id: UUID
    episode_id: Optional[UUID] = None
    video_file_id: Optional[UUID] = None
    sheet_source: Optional[str] = None
    sheet_row_number: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Tag schemas
class TagBase(BaseModel):
    """Tag base schema."""

    category: str
    name: str
    name_display: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0


class TagCreate(TagBase):
    """Tag create schema."""

    pass


class TagUpdate(BaseModel):
    """Tag update schema."""

    name_display: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class TagResponse(TagBase, BaseSchema):
    """Tag response schema."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TagWithCountResponse(TagResponse):
    """Tag with usage count."""

    usage_count: int


# Player schemas
class PlayerBase(BaseModel):
    """Player base schema."""

    name: str
    name_display: Optional[str] = None
    nationality: Optional[str] = None
    hendon_mob_id: Optional[str] = None
    total_live_earnings: Optional[Decimal] = None
    wsop_bracelets: Optional[int] = 0


class PlayerCreate(PlayerBase):
    """Player create schema."""

    pass


class PlayerUpdate(BaseModel):
    """Player update schema."""

    name_display: Optional[str] = None
    nationality: Optional[str] = None
    hendon_mob_id: Optional[str] = None
    total_live_earnings: Optional[Decimal] = None
    wsop_bracelets: Optional[int] = None
    is_active: Optional[bool] = None


class PlayerResponse(PlayerBase, BaseSchema):
    """Player response schema."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PlayerWithCountResponse(PlayerResponse):
    """Player with appearance count."""

    appearance_count: int


# NAS Folder schemas
class NASFolderBase(BaseModel):
    """NAS Folder base schema."""

    folder_path: str
    folder_name: str
    parent_path: Optional[str] = None
    depth: int = 0


class NASFolderCreate(NASFolderBase):
    """NAS Folder create schema."""

    is_hidden_folder: bool = False


class NASFolderUpdate(BaseModel):
    """NAS Folder update schema."""

    file_count: Optional[int] = None
    folder_count: Optional[int] = None
    total_size_bytes: Optional[int] = None
    is_hidden_folder: Optional[bool] = None


class NASFolderResponse(NASFolderBase, BaseSchema):
    """NAS Folder response schema."""

    id: UUID
    file_count: int
    folder_count: int
    total_size_bytes: int
    is_empty: bool
    is_hidden_folder: bool
    created_at: datetime
    updated_at: datetime


class NASFolderStatsResponse(BaseModel):
    """NAS Folder statistics response."""

    total_folders: int
    total_files: int
    total_size_bytes: int
    empty_folders: int
    hidden_folders: int


# NAS File schemas
class NASFileBase(BaseModel):
    """NAS File base schema."""

    file_path: str
    file_name: str
    file_extension: Optional[str] = None
    file_category: str = "other"


class NASFileCreate(NASFileBase):
    """NAS File create schema."""

    file_size_bytes: int = 0
    folder_id: Optional[UUID] = None
    file_mtime: Optional[datetime] = None
    is_hidden_file: bool = False


class NASFileUpdate(BaseModel):
    """NAS File update schema."""

    file_size_bytes: Optional[int] = None
    file_mtime: Optional[datetime] = None
    file_category: Optional[str] = None
    is_hidden_file: Optional[bool] = None
    video_file_id: Optional[UUID] = None


class NASFileResponse(NASFileBase, BaseSchema):
    """NAS File response schema."""

    id: UUID
    file_size_bytes: int
    file_mtime: Optional[datetime]
    is_hidden_file: bool
    folder_id: Optional[UUID]
    video_file_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class NASFileStatsResponse(BaseModel):
    """NAS File statistics response."""

    total_files: int
    total_size_bytes: int
    by_category: dict[str, int]
    by_extension: dict[str, int]
    linked_count: int
    unlinked_count: int


# Pagination
class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    total: int
    skip: int
    limit: int
    items: list


# ==================== Auth Schemas ====================


class UserStatus(str):
    """User status enum."""

    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class UserRole(str):
    """User role enum."""

    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    """User base schema."""

    username: str


class UserCreate(UserBase):
    """User create schema."""

    password: str


class UserLogin(BaseModel):
    """User login schema."""

    username: str
    password: str


class UserResponse(UserBase, BaseSchema):
    """User response schema."""

    id: UUID
    role: str
    status: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None


class UserStatusUpdate(BaseModel):
    """User status update schema."""

    status: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== Contents Schemas (Netflix-style) ====================


class ContentItem(BaseModel):
    """Netflix-style content item for browse page."""

    id: UUID
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    category: str
    year: Optional[int] = None
    duration_seconds: Optional[int] = None
    quality: Optional[str] = None
    tags: list[str] = []
    progress: Optional[float] = None  # 0-100 for continue watching


class FeaturedContent(ContentItem):
    """Featured content for hero billboard."""

    players: list[str] = []
    event_type: Optional[str] = None


class ContentRow(BaseModel):
    """Content row for browse page."""

    title: str
    items: list[ContentItem]
    row_type: str = "default"  # default, continue-watching, top10


class BrowseResponse(BaseModel):
    """Browse page response."""

    featured: Optional[FeaturedContent] = None
    rows: list[ContentRow]


class Top10Item(ContentItem):
    """Top 10 content item with rank."""

    rank: int


# ==================== Watch Progress Schemas ====================


class WatchProgressCreate(BaseModel):
    """Watch progress create schema."""

    content_id: UUID
    position_seconds: int
    duration_seconds: Optional[int] = None


class WatchProgressResponse(BaseModel):
    """Watch progress response schema."""

    user_id: UUID
    content_id: UUID
    position_seconds: int
    duration_seconds: Optional[int] = None
    progress_percent: float
    is_completed: bool
    updated_at: datetime


class ContinueWatchingItem(ContentItem):
    """Continue watching item with progress."""

    position_seconds: int
    last_watched: datetime


# ==================== Catalog Item Schemas ====================


class CatalogItemBase(BaseModel):
    """Catalog item base schema."""

    display_title: str
    catalog_title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    project_code: str
    category: Optional[str] = None
    content_type: Optional[str] = None
    tags: Optional[list[str]] = None
    year: Optional[int] = None
    event_number: Optional[int] = None
    episode_number: Optional[int] = None
    day_number: Optional[int] = None


class CatalogItemResponse(CatalogItemBase, BaseSchema):
    """Catalog item response schema."""

    id: UUID
    video_file_id: UUID
    episode_id: Optional[UUID] = None
    featured_rank: Optional[int] = None
    top10_rank: Optional[int] = None
    is_published: bool
    is_featured: bool
    extra_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class CatalogItemCreate(BaseModel):
    """Catalog item create schema."""

    video_file_id: UUID
    display_title: Optional[str] = None
    is_featured: bool = False
    featured_rank: Optional[int] = None
    top10_rank: Optional[int] = None


class CatalogItemUpdate(BaseModel):
    """Catalog item update schema."""

    display_title: Optional[str] = None
    catalog_title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    featured_rank: Optional[int] = None
    top10_rank: Optional[int] = None


class CatalogBrowseResponse(BaseModel):
    """Catalog browse response with CatalogItem."""

    featured: Optional[CatalogItemResponse] = None
    rows: list[ContentRow]
    total: int
