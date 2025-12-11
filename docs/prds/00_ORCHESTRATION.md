# PRD: PokerVOD 오케스트레이션 레이어

> **버전**: 1.0.0 | **작성일**: 2025-12-11 | **상태**: Draft

---

## 1. 개요

### 1.1 목적

PokerVOD 시스템의 **7개 블럭(에이전트)**를 중앙에서 조율하는 오케스트레이션 레이어입니다.
각 블럭은 독립적으로 동작하며, 오케스트레이션 레이어가 상호 정보 교환과 실행 순서를 관리합니다.

### 1.2 설계 원칙

| 원칙 | 설명 |
|------|------|
| **느슨한 결합** | 블럭 간 직접 의존 금지, 이벤트 버스로 통신 |
| **독립 실행** | 각 블럭은 단독으로 테스트/배포 가능 |
| **장애 격리** | 한 블럭 실패가 전체 시스템 중단 방지 |
| **확장성** | 새 블럭 추가 시 기존 코드 수정 최소화 |

---

## 2. 블럭 구조

### 2.1 전체 블럭 목록 (7개)

| 코드 | 블럭명 | 역할 | 의존성 |
|------|--------|------|--------|
| A | NAS Inventory Agent | 파일 스캔 & 파싱 | 없음 (독립) |
| B | Catalog Agent | 프로젝트/시즌/이벤트 구조 | 없음 (독립) |
| C | Hand Analysis Agent | 핸드 분석 & 태그 관리 | B (에피소드) |
| D | Sheets Sync Agent | Google Sheets 동기화 | A, B (매칭) |
| E | API Agent | REST API 제공 | A, B, C, D (읽기) |
| F | Dashboard Agent | 프론트엔드 UI | E (API) |
| G | Database Agent | DB & 마이그레이션 | 모든 블럭 기반 |

### 2.2 의존성 그래프

```
                    ┌───────────────────────────────────────┐
                    │         오케스트레이션 레이어           │
                    │    (EventBus, Scheduler, Monitor)     │
                    └───────────────────┬───────────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │                            │                            │
           ▼                            ▼                            ▼
    ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
    │  블럭 A     │              │  블럭 B     │              │  블럭 G     │
    │ NAS Agent   │              │Catalog Agent│              │Database     │
    └──────┬──────┘              └──────┬──────┘              └─────────────┘
           │                            │                            ▲
           │                            │                            │
           │         ┌──────────────────┴──────────────────┐        │
           │         │                                      │        │
           │         ▼                                      ▼        │
           │  ┌─────────────┐                       ┌─────────────┐  │
           │  │  블럭 C     │                       │  블럭 D     │◀─┘
           │  │Hand Analysis│                       │Sheets Sync  │
           │  └──────┬──────┘                       └──────┬──────┘
           │         │                                      │
           └─────────┼──────────────────────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │  블럭 E     │
              │ API Agent   │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │  블럭 F     │
              │Dashboard    │
              └─────────────┘
```

---

## 3. 이벤트 버스

### 3.1 이벤트 정의

```python
class EventType(Enum):
    # NAS 관련
    NAS_SCAN_REQUESTED = "nas.scan.requested"
    NAS_SCAN_COMPLETED = "nas.scan.completed"
    NAS_FILE_ADDED = "nas.file.added"
    NAS_FILE_REMOVED = "nas.file.removed"

    # 카탈로그 관련
    CATALOG_UPDATE_REQUESTED = "catalog.update.requested"
    CATALOG_UPDATED = "catalog.updated"
    PROJECT_CREATED = "catalog.project.created"
    EPISODE_CREATED = "catalog.episode.created"

    # Sheets 관련
    SHEETS_SYNC_REQUESTED = "sheets.sync.requested"
    SHEETS_SYNC_COMPLETED = "sheets.sync.completed"
    SHEETS_ROW_CHANGED = "sheets.row.changed"

    # 핸드 분석 관련
    HAND_CLIP_CREATED = "hand.clip.created"
    HAND_CLIP_TAGGED = "hand.clip.tagged"

    # 시스템 관련
    SYNC_ALL_REQUESTED = "system.sync.all"
    SYNC_ALL_COMPLETED = "system.sync.completed"
    ERROR_OCCURRED = "system.error"
```

### 3.2 이벤트 페이로드

```python
@dataclass
class Event:
    type: EventType
    payload: dict
    timestamp: datetime
    source_block: str  # A, B, C, D, E, F, G
    correlation_id: str  # 트랜잭션 추적용
```

### 3.3 이벤트 핸들러 등록

```python
class EventBus:
    def __init__(self):
        self._handlers: dict[EventType, list[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable):
        """이벤트 구독"""
        self._handlers.setdefault(event_type, []).append(handler)

    async def emit(self, event: Event):
        """이벤트 발행"""
        for handler in self._handlers.get(event.type, []):
            await handler(event)
```

---

## 4. 동기화 플로우

### 4.1 전체 동기화 (Initial Sync)

```python
async def sync_all(self):
    """전체 동기화 - 시스템 초기화 또는 강제 새로고침"""
    correlation_id = str(uuid4())

    # Phase 1: 기초 데이터 (병렬 실행)
    await asyncio.gather(
        self.emit(Event(NAS_SCAN_REQUESTED, {}, block="A", cid=correlation_id)),
        self.emit(Event(CATALOG_UPDATE_REQUESTED, {}, block="B", cid=correlation_id)),
    )

    # Phase 2: 동기화 (A, B 완료 대기 후)
    await self.wait_for([NAS_SCAN_COMPLETED, CATALOG_UPDATED])
    await self.emit(Event(SHEETS_SYNC_REQUESTED, {}, block="D", cid=correlation_id))

    # Phase 3: 분석 (D 완료 대기 후)
    await self.wait_for([SHEETS_SYNC_COMPLETED])
    await self.emit(Event(HAND_CLIP_TAGGED, {}, block="C", cid=correlation_id))

    # Phase 4: 캐시 갱신
    await self.emit(Event(SYNC_ALL_COMPLETED, {}, block="orchestrator", cid=correlation_id))
```

### 4.2 증분 동기화 (Incremental Sync)

```python
async def on_sheets_row_changed(self, event: Event):
    """Sheets 변경 감지 시 증분 동기화"""
    row_data = event.payload["row"]

    # 파일 경로 매칭 (블럭 A 데이터)
    video_file = await self.blocks["A"].match_file_path(row_data["nas_folder_link"])

    # 에피소드 매칭 (블럭 B 데이터)
    episode = await self.blocks["B"].match_episode(row_data["file_name"])

    # 핸드 클립 생성 (블럭 C)
    await self.blocks["C"].create_hand_clip(
        video_file_id=video_file.id,
        episode_id=episode.id,
        timecode=row_data["in"],
        timecode_end=row_data["out"],
        tags=row_data["tags"],
    )
```

---

## 5. 에이전트 인터페이스

### 5.1 기본 에이전트 계약

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """모든 블럭 에이전트의 기본 인터페이스"""

    def __init__(self, event_bus: EventBus, db_session: AsyncSession):
        self.event_bus = event_bus
        self.db = db_session
        self.block_id: str  # A, B, C, D, E, F, G

    @abstractmethod
    async def initialize(self):
        """에이전트 초기화"""
        pass

    @abstractmethod
    async def process(self, event: Event) -> dict:
        """이벤트 처리"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """상태 체크"""
        pass

    async def emit(self, event_type: EventType, payload: dict):
        """이벤트 발행 헬퍼"""
        event = Event(
            type=event_type,
            payload=payload,
            timestamp=datetime.utcnow(),
            source_block=self.block_id,
            correlation_id=self._current_correlation_id,
        )
        await self.event_bus.emit(event)
```

### 5.2 에이전트별 인터페이스

| 블럭 | 주요 메서드 | 입력 | 출력 |
|------|------------|------|------|
| A | `scan_nas()` | NAS 경로 | `list[NASFile]` |
| A | `parse_filename(name)` | 파일명 | `ParsedMetadata` |
| B | `create_project(code, name)` | 프로젝트 정보 | `Project` |
| B | `match_episode(title)` | 영상 제목 | `Episode` |
| C | `create_hand_clip(...)` | 클립 정보 | `HandClip` |
| C | `add_tags(clip_id, tags)` | 클립 ID, 태그 | `list[Tag]` |
| D | `sync_sheet(sheet_id)` | Sheet ID | `SyncResult` |
| D | `match_file_path(path)` | NAS 경로 | `VideoFile` |
| E | `list_projects()` | - | `list[ProjectDTO]` |
| E | `search_catalog(query)` | 검색어 | `list[CatalogItem]` |
| F | `render_catalog()` | - | React Component |
| G | `run_migration()` | - | `MigrationResult` |

---

## 6. 상태 관리

### 6.1 동기화 상태 추적

```python
class SyncStatus(Enum):
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # 일부 성공

@dataclass
class BlockStatus:
    block_id: str
    status: SyncStatus
    last_sync_at: datetime | None
    last_error: str | None
    items_processed: int
    items_total: int

class StatusTracker:
    def __init__(self):
        self.blocks: dict[str, BlockStatus] = {}
        self.correlation_logs: dict[str, list[Event]] = {}

    def update_status(self, block_id: str, status: SyncStatus):
        self.blocks[block_id].status = status

    def get_overall_status(self) -> SyncStatus:
        """전체 시스템 상태 반환"""
        statuses = [b.status for b in self.blocks.values()]
        if all(s == SyncStatus.COMPLETED for s in statuses):
            return SyncStatus.COMPLETED
        if any(s == SyncStatus.FAILED for s in statuses):
            return SyncStatus.PARTIAL
        if any(s == SyncStatus.IN_PROGRESS for s in statuses):
            return SyncStatus.IN_PROGRESS
        return SyncStatus.IDLE
```

### 6.2 모니터링 엔드포인트

```python
@router.get("/api/orchestrator/status")
async def get_orchestrator_status():
    return {
        "overall": status_tracker.get_overall_status(),
        "blocks": {
            "A": status_tracker.blocks["A"].dict(),
            "B": status_tracker.blocks["B"].dict(),
            # ...
        },
        "last_sync": status_tracker.last_full_sync,
        "next_scheduled_sync": scheduler.next_run,
    }
```

---

## 7. 에러 처리

### 7.1 재시도 정책

```python
RETRY_POLICIES = {
    "A": RetryPolicy(max_attempts=3, backoff="exponential", base_delay=5),
    "B": RetryPolicy(max_attempts=3, backoff="exponential", base_delay=5),
    "C": RetryPolicy(max_attempts=2, backoff="fixed", base_delay=2),
    "D": RetryPolicy(max_attempts=5, backoff="exponential", base_delay=10),  # Sheets API 제한
    "E": RetryPolicy(max_attempts=1, circuit_breaker=True),
    "F": RetryPolicy(max_attempts=0),  # 클라이언트 재시도
    "G": RetryPolicy(max_attempts=1, rollback_on_fail=True),
}
```

### 7.2 Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time: datetime | None = None

    async def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_try_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

### 7.3 장애 격리

```python
async def on_block_failure(self, block_id: str, error: Exception):
    """블럭 실패 시 처리"""
    # 1. 해당 블럭만 FAILED로 표시
    self.status_tracker.update_status(block_id, SyncStatus.FAILED)

    # 2. 의존 블럭에 알림
    dependent_blocks = DEPENDENCY_GRAPH.get(block_id, [])
    for dep in dependent_blocks:
        await self.emit(Event(
            type=EventType.ERROR_OCCURRED,
            payload={"source": block_id, "error": str(error)},
            source_block="orchestrator",
        ))

    # 3. 대체 전략 실행 (있는 경우)
    fallback = FALLBACK_STRATEGIES.get(block_id)
    if fallback:
        await fallback(error)
```

---

## 8. 스케줄러

### 8.1 정기 동기화

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# 매일 새벽 3시 전체 동기화
scheduler.add_job(orchestrator.sync_all, "cron", hour=3)

# 5분마다 Sheets 증분 동기화
scheduler.add_job(orchestrator.sync_sheets_incremental, "interval", minutes=5)

# 1시간마다 NAS 변경 감지
scheduler.add_job(orchestrator.detect_nas_changes, "interval", hours=1)
```

### 8.2 수동 트리거

```python
@router.post("/api/orchestrator/sync")
async def trigger_sync(sync_type: str = "incremental"):
    if sync_type == "full":
        task = asyncio.create_task(orchestrator.sync_all())
    else:
        task = asyncio.create_task(orchestrator.sync_incremental())

    return {"task_id": id(task), "status": "started"}
```

---

## 9. 성능 요구사항

| 지표 | 목표 |
|------|------|
| 전체 동기화 시간 | < 10분 (1,400 파일 기준) |
| 증분 동기화 지연 | < 60초 |
| 이벤트 처리 지연 | < 100ms |
| 블럭 간 통신 오버헤드 | < 10ms |
| 메모리 사용량 | < 512MB (오케스트레이터) |

---

## 10. 프로젝트 구조

```
backend/src/orchestrator/
├── __init__.py
├── event_bus.py           # 이벤트 버스 구현
├── events.py              # 이벤트 타입 정의
├── status.py              # 상태 추적
├── scheduler.py           # 스케줄러
├── circuit_breaker.py     # Circuit Breaker
├── retry.py               # 재시도 정책
└── orchestrator.py        # 메인 오케스트레이터
```

---

## 11. 테스트 전략

### 11.1 단위 테스트

```python
# tests/orchestrator/test_event_bus.py
async def test_event_subscription():
    bus = EventBus()
    received = []

    bus.subscribe(EventType.NAS_SCAN_COMPLETED, lambda e: received.append(e))
    await bus.emit(Event(type=EventType.NAS_SCAN_COMPLETED, payload={"count": 100}))

    assert len(received) == 1
    assert received[0].payload["count"] == 100
```

### 11.2 통합 테스트

```python
# tests/orchestrator/test_sync_flow.py
async def test_full_sync_flow():
    orchestrator = Orchestrator()

    # Mock 블럭들
    orchestrator.blocks["A"] = MockNASAgent()
    orchestrator.blocks["B"] = MockCatalogAgent()

    await orchestrator.sync_all()

    assert orchestrator.status_tracker.get_overall_status() == SyncStatus.COMPLETED
```

---

**문서 버전**: 1.0.0
**작성일**: 2025-12-11
