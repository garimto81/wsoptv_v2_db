"""Status Tracker - 오케스트레이션 레이어."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SyncStatus(str, Enum):
    """동기화 상태."""

    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class BlockStatus:
    """블럭별 상태."""

    block_id: str
    status: SyncStatus = SyncStatus.IDLE
    last_sync_at: Optional[datetime] = None
    last_error: Optional[str] = None
    items_processed: int = 0
    items_total: int = 0
    progress_percent: float = 0.0

    def update_progress(self, processed: int, total: int) -> None:
        """진행률 업데이트."""
        self.items_processed = processed
        self.items_total = total
        self.progress_percent = (processed / total * 100) if total > 0 else 0.0


@dataclass
class StatusTracker:
    """전체 시스템 상태 추적."""

    blocks: dict[str, BlockStatus] = field(default_factory=dict)
    last_full_sync: Optional[datetime] = None
    next_scheduled_sync: Optional[datetime] = None

    def __post_init__(self):
        # 7개 블럭 초기화
        for block_id in ["A", "B", "C", "D", "E", "F", "G"]:
            self.blocks[block_id] = BlockStatus(block_id=block_id)

    def update_status(self, block_id: str, status: SyncStatus) -> None:
        """블럭 상태 업데이트."""
        if block_id in self.blocks:
            self.blocks[block_id].status = status
            if status == SyncStatus.COMPLETED:
                self.blocks[block_id].last_sync_at = datetime.utcnow()

    def update_error(self, block_id: str, error: str) -> None:
        """에러 기록."""
        if block_id in self.blocks:
            self.blocks[block_id].last_error = error
            self.blocks[block_id].status = SyncStatus.FAILED

    def get_overall_status(self) -> SyncStatus:
        """전체 시스템 상태 반환."""
        statuses = [b.status for b in self.blocks.values()]

        if all(s == SyncStatus.COMPLETED for s in statuses):
            return SyncStatus.COMPLETED
        if any(s == SyncStatus.FAILED for s in statuses):
            return SyncStatus.PARTIAL
        if any(s == SyncStatus.IN_PROGRESS for s in statuses):
            return SyncStatus.IN_PROGRESS
        return SyncStatus.IDLE

    def to_dict(self) -> dict:
        """딕셔너리 변환."""
        return {
            "overall": self.get_overall_status().value,
            "blocks": {
                block_id: {
                    "status": block.status.value,
                    "last_sync_at": block.last_sync_at.isoformat()
                    if block.last_sync_at
                    else None,
                    "last_error": block.last_error,
                    "items_processed": block.items_processed,
                    "items_total": block.items_total,
                    "progress_percent": round(block.progress_percent, 1),
                }
                for block_id, block in self.blocks.items()
            },
            "last_full_sync": self.last_full_sync.isoformat()
            if self.last_full_sync
            else None,
            "next_scheduled_sync": self.next_scheduled_sync.isoformat()
            if self.next_scheduled_sync
            else None,
        }


# 싱글톤 인스턴스
_status_tracker: Optional[StatusTracker] = None


def get_status_tracker() -> StatusTracker:
    """StatusTracker 싱글톤 인스턴스 반환."""
    global _status_tracker
    if _status_tracker is None:
        _status_tracker = StatusTracker()
    return _status_tracker
