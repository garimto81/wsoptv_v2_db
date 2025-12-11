"""Base Agent - 오케스트레이션 레이어."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .event_bus import EventBus, get_event_bus
from .events import Event, EventType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """모든 블럭 에이전트의 기본 클래스.

    각 블럭 에이전트는 이 클래스를 상속받아 구현합니다.
    """

    # 블럭 ID (A, B, C, D, E, F, G)
    block_id: str = ""

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.db = db
        self.event_bus = event_bus or get_event_bus()
        self._current_correlation_id: Optional[str] = None

        # 이벤트 핸들러 자동 등록
        self._register_handlers()

    def _register_handlers(self) -> None:
        """이벤트 핸들러 등록."""
        # 서브클래스에서 오버라이드
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """에이전트 초기화."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """상태 체크."""
        pass

    async def emit(
        self,
        event_type: EventType,
        payload: dict,
        parent_event_id: Optional[str] = None,
    ) -> None:
        """이벤트 발행 헬퍼."""
        event = Event(
            type=event_type,
            payload=payload,
            source_block=self.block_id,
            correlation_id=self._current_correlation_id or "",
            parent_event_id=parent_event_id,
        )
        await self.event_bus.emit(event)

    def set_correlation_id(self, correlation_id: str) -> None:
        """현재 트랜잭션의 correlation_id 설정."""
        self._current_correlation_id = correlation_id

    def clear_correlation_id(self) -> None:
        """correlation_id 초기화."""
        self._current_correlation_id = None

    async def on_error(self, error: Exception, context: dict) -> None:
        """에러 발생 시 처리."""
        logger.error(f"[{self.block_id}] Error: {error}, Context: {context}")
        await self.emit(
            EventType.ERROR_OCCURRED,
            {
                "block_id": self.block_id,
                "error": str(error),
                "error_type": type(error).__name__,
                "context": context,
            },
        )


class AgentStatus:
    """에이전트 상태."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
