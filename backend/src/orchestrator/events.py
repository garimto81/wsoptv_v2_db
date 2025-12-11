"""Event Types - 오케스트레이션 레이어."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class EventType(str, Enum):
    """시스템 이벤트 타입."""

    # NAS 관련 (블럭 A)
    NAS_SCAN_REQUESTED = "nas.scan.requested"
    NAS_SCAN_COMPLETED = "nas.scan.completed"
    NAS_FILE_ADDED = "nas.file.added"
    NAS_FILE_REMOVED = "nas.file.removed"
    NAS_FILE_CHANGED = "nas.file.changed"

    # 카탈로그 관련 (블럭 B)
    CATALOG_UPDATE_REQUESTED = "catalog.update.requested"
    CATALOG_UPDATED = "catalog.updated"
    PROJECT_CREATED = "catalog.project.created"
    SEASON_CREATED = "catalog.season.created"
    EVENT_CREATED = "catalog.event.created"
    EPISODE_CREATED = "catalog.episode.created"

    # 핸드 분석 관련 (블럭 C)
    HAND_CLIP_CREATED = "hand.clip.created"
    HAND_CLIP_UPDATED = "hand.clip.updated"
    HAND_CLIP_TAGGED = "hand.clip.tagged"
    PLAYER_LINKED = "hand.player.linked"

    # Sheets 동기화 관련 (블럭 D)
    SHEETS_SYNC_REQUESTED = "sheets.sync.requested"
    SHEETS_SYNC_COMPLETED = "sheets.sync.completed"
    SHEETS_ROW_CHANGED = "sheets.row.changed"
    SHEETS_SYNC_FAILED = "sheets.sync.failed"

    # API 관련 (블럭 E)
    API_CACHE_REFRESH = "api.cache.refresh"

    # 시스템 관련
    SYNC_ALL_REQUESTED = "system.sync.all.requested"
    SYNC_ALL_COMPLETED = "system.sync.all.completed"
    ERROR_OCCURRED = "system.error"
    BLOCK_STATUS_CHANGED = "system.block.status"


@dataclass
class Event:
    """시스템 이벤트."""

    type: EventType
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_block: str = ""  # A, B, C, D, E, F, G, orchestrator
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    parent_event_id: Optional[str] = None

    def to_dict(self) -> dict:
        """딕셔너리 변환."""
        return {
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "source_block": self.source_block,
            "correlation_id": self.correlation_id,
            "parent_event_id": self.parent_event_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """딕셔너리에서 생성."""
        return cls(
            type=EventType(data["type"]),
            payload=data.get("payload", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_block=data.get("source_block", ""),
            correlation_id=data.get("correlation_id", str(uuid4())),
            parent_event_id=data.get("parent_event_id"),
        )
