"""GoogleSheetSync model - 블럭 D (Sheets Sync Agent)."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class GoogleSheetSync(Base, TimestampMixin):
    """Google Sheets 동기화 상태 추적."""

    __tablename__ = "google_sheet_sync"
    __table_args__ = (
        UniqueConstraint("sheet_id", "entity_type"),
        {"schema": "pokervod"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    sheet_id: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    last_row_synced: Mapped[int] = mapped_column(default=0)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    sync_status: Mapped[str] = mapped_column(String(20), default="idle")
    error_message: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    def __repr__(self) -> str:
        return f"<GoogleSheetSync(sheet={self.sheet_id}, entity={self.entity_type})>"


# Sheet IDs
class SheetId:
    METADATA_ARCHIVE = "1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4"
    ICONIK_METADATA = "1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk"


# Sync Status
class SyncStatus:
    IDLE = "idle"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
