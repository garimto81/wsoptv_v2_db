"""Event Bus - 오케스트레이션 레이어."""

import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Optional

from .events import Event, EventType

logger = logging.getLogger(__name__)

# 이벤트 핸들러 타입
EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """비동기 이벤트 버스.

    블럭 간 느슨한 결합을 위한 이벤트 기반 통신을 제공합니다.
    """

    def __init__(self):
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._event_history: list[Event] = []
        self._max_history = 1000

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """이벤트 구독."""
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type.value}: {handler.__name__}")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """이벤트 구독 해제."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed from {event_type.value}: {handler.__name__}")

    async def emit(self, event: Event) -> None:
        """이벤트 발행."""
        # 히스토리에 추가
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        logger.info(
            f"Event emitted: {event.type.value} from {event.source_block} "
            f"(correlation: {event.correlation_id[:8]})"
        )

        # 핸들러 실행
        handlers = self._handlers.get(event.type, [])
        if not handlers:
            logger.debug(f"No handlers for {event.type.value}")
            return

        # 모든 핸들러 병렬 실행
        tasks = [self._safe_call(handler, event) for handler in handlers]
        await asyncio.gather(*tasks)

    async def _safe_call(self, handler: EventHandler, event: Event) -> None:
        """안전한 핸들러 호출."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Error in handler {handler.__name__} for {event.type.value}: {e}"
            )
            # 에러 이벤트 발행
            error_event = Event(
                type=EventType.ERROR_OCCURRED,
                payload={
                    "original_event": event.type.value,
                    "handler": handler.__name__,
                    "error": str(e),
                },
                source_block="event_bus",
                parent_event_id=event.correlation_id,
            )
            # 재귀 방지
            if event.type != EventType.ERROR_OCCURRED:
                await self.emit(error_event)

    def get_history(
        self, event_type: Optional[EventType] = None, limit: int = 100
    ) -> list[Event]:
        """이벤트 히스토리 조회."""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]

    def get_handlers_count(self, event_type: EventType) -> int:
        """특정 이벤트의 핸들러 수."""
        return len(self._handlers.get(event_type, []))

    def clear_handlers(self) -> None:
        """모든 핸들러 제거."""
        self._handlers.clear()


# 싱글톤 인스턴스
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """EventBus 싱글톤 인스턴스 반환."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
