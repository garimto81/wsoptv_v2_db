# PRD: 블럭 D - Sheets Sync Agent

> **버전**: 1.0.0 | **작성일**: 2025-12-11 | **블럭 코드**: D

---

## 1. 개요

### 1.1 목적

Google Sheets 데이터를 PostgreSQL과 동기화합니다. 2개 시트의 핸드 분석 데이터를 정규화하여 DB에 반영합니다.

### 1.2 책임 범위

| 항목 | 포함 | 제외 |
|------|------|------|
| Sheets API 연결 | O | |
| 증분 동기화 | O | |
| 데이터 정규화 | O | |
| file_path ↔ VideoFile 매칭 | O | |
| title ↔ Episode 매칭 | O | |
| NAS 스캔 | | X (블럭 A) |
| 핸드 클립 저장 | | X (블럭 C) |

---

## 2. 데이터 소스

### 2.1 Sheet 1: metadata_archive (핸드 분석)

**시트 ID**: `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4`
**행 수**: 40+

| # | 컬럼명 | DB 매핑 |
|---|--------|---------|
| 1 | File No. | `hand_clips.clip_number` |
| 2 | File Name | 에피소드 매칭용 |
| 3 | **Nas Folder Link** | `video_files.file_path` (**핵심**) |
| 4 | In | `hand_clips.timecode` |
| 5 | Out | `hand_clips.timecode_end` |
| 6 | Hand Grade | `hand_clips.hand_grade` |
| 7 | Winner | `hand_clips.winner_hand` |
| 8 | Hands | `hand_clips.hands_involved` |
| 9-11 | Tag (Player) 1~3 | `hand_clip_players` (N:N) |
| 12-19 | Tag (Poker Play) 1~7 | `hand_clip_tags` (poker_play) |
| 20-21 | Tag (Emotion) 1~2 | `hand_clip_tags` (emotion) |

### 2.2 Sheet 2: iconik_metadata (핸드 DB)

**시트 ID**: `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk`
**행 수**: 2,500+

| # | 컬럼명 | DB 매핑 |
|---|--------|---------|
| 1 | id | `hand_clips.id` (UUID) |
| 2 | title | `hand_clips.title` |
| 3 | time_start_ms | `hand_clips.start_seconds` |
| 4 | time_end_ms | `hand_clips.end_seconds` |
| 5 | Description | `hand_clips.description` |
| 6 | ProjectName | `projects.code` |
| 7 | Year_ | `seasons.year` |
| 8 | Location | `seasons.location` |
| 9 | Venue | `events.name` |
| 10 | Source | `video_files.version_type` |
| 11 | PlayersTags | 쉼표 구분 → `players` |
| 12 | HandGrade | `hand_clips.hand_grade` |
| 13 | HANDTag | `hand_clips.hands_involved` |
| 14 | PokerPlayTags | 쉼표 구분 → `tags` (poker_play) |
| 15 | Emotion | 쉼표 구분 → `tags` (emotion) |
| 16 | GameType | `events.game_type` |
| 17 | RUNOUTTag | `tags` (runout) |
| 18 | EPICHAND | `tags` (epic_hand) |
| 19 | Adjective | `tags` (adjective) |

---

## 3. 동기화 전략

### 3.1 증분 동기화

```python
class IncrementalSync:
    def __init__(self, sheet_id: str, entity_type: str):
        self.sheet_id = sheet_id
        self.entity_type = entity_type

    async def get_last_synced_row(self) -> int:
        """마지막 동기화 행 번호 조회"""
        sync_state = await self.db.get(GoogleSheetSync, {
            "sheet_id": self.sheet_id,
            "entity_type": self.entity_type,
        })
        return sync_state.last_row_synced if sync_state else 0

    async def sync(self):
        """증분 동기화 실행"""
        last_row = await self.get_last_synced_row()

        # 새 행만 가져오기
        new_rows = await self.sheets_client.get_rows(
            sheet_id=self.sheet_id,
            start_row=last_row + 1,
        )

        for row in new_rows:
            await self.process_row(row)

        # 상태 업데이트
        await self.update_sync_state(last_row + len(new_rows))
```

### 3.2 전체 동기화

```python
async def full_sync(self, sheet_id: str):
    """전체 동기화 (초기화 또는 강제 리프레시)"""
    # 1. 기존 데이터 soft delete
    await self.mark_existing_as_stale(sheet_id)

    # 2. 전체 행 동기화
    all_rows = await self.sheets_client.get_all_rows(sheet_id)
    for row in all_rows:
        await self.process_row(row, is_full_sync=True)

    # 3. 동기화 상태 초기화
    await self.reset_sync_state(sheet_id)
```

---

## 4. 데이터 매칭

### 4.1 file_path 매칭 (블럭 A 데이터)

```python
async def match_by_file_path(self, nas_folder_link: str) -> VideoFile | None:
    """
    Sheet의 Nas Folder Link → VideoFile 매칭

    예시:
    Input: "\\10.10.100.122\docker\GGPNAs\ARCHIVE\WSOP\2024..."
    Output: VideoFile(file_path="\\10.10.100.122\docker\GGPNAs\ARCHIVE\WSOP\2024...")
    """
    # 1. 정확한 경로 매칭
    video_file = await self.db.execute(
        select(VideoFile).filter(VideoFile.file_path == nas_folder_link)
    )
    if video_file:
        return video_file

    # 2. 정규화 후 매칭 (경로 구분자 차이 등)
    normalized_path = self._normalize_path(nas_folder_link)
    video_file = await self.db.execute(
        select(VideoFile).filter(
            func.replace(VideoFile.file_path, "/", "\\") == normalized_path
        )
    )

    return video_file
```

### 4.2 title 매칭 (블럭 B 데이터)

```python
async def match_by_title(self, file_name: str, project_code: str | None = None) -> Episode | None:
    """
    Sheet의 File Name → Episode 매칭
    """
    # 1. 파일명 파싱
    parsed = ParserFactory.get_parser(file_name).parse(file_name)

    # 2. 블럭 B 매칭 호출
    return await self.catalog_agent.match_episode(file_name, parsed)
```

---

## 5. 데이터 정규화

### 5.1 다중 값 분리

```python
def split_multi_value(value: str) -> list[str]:
    """쉼표 구분 값 분리"""
    if not value:
        return []

    # 쉼표, 세미콜론, 파이프로 분리
    items = re.split(r"[,;|]", value)

    # 공백 제거 및 빈 값 필터
    return [item.strip() for item in items if item.strip()]

# 사용 예시
players = split_multi_value("Phil Hellmuth, Daniel Negreanu, Phil Ivey")
# ["Phil Hellmuth", "Daniel Negreanu", "Phil Ivey"]
```

### 5.2 태그 정규화

```python
async def normalize_and_create_tags(
    self,
    raw_values: list[str],
    category: str,
) -> list[Tag]:
    """태그 정규화 및 생성"""
    tags = []
    for raw in raw_values:
        # 정규화
        name = normalize_tag(raw, category)

        # 기존 태그 찾기 또는 생성
        tag = await self.find_or_create_tag(category, name, display_name=raw)
        tags.append(tag)

    return tags
```

### 5.3 타임코드 변환

```python
def convert_timecode(value: str | int) -> str:
    """다양한 형식 → H:MM:SS 변환"""
    if isinstance(value, int):
        # 밀리초 → H:MM:SS
        seconds = value // 1000
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h}:{m:02d}:{s:02d}"

    if isinstance(value, str) and value.isdigit():
        return convert_timecode(int(value))

    # 이미 H:MM:SS 형식
    return value
```

---

## 6. API

### 6.1 에이전트 인터페이스

```python
class SheetsSyncAgent(BaseAgent):
    block_id = "D"

    async def sync_sheet(
        self,
        sheet_id: str,
        sync_type: str = "incremental",  # incremental, full
    ) -> SyncResult:
        """시트 동기화"""
        pass

    async def sync_all_sheets(self) -> list[SyncResult]:
        """모든 시트 동기화"""
        pass

    async def match_file_path(self, path: str) -> VideoFile | None:
        """file_path로 VideoFile 매칭"""
        pass

    async def match_title(self, title: str) -> Episode | None:
        """제목으로 Episode 매칭"""
        pass

    async def preview_sheet(self, sheet_id: str, limit: int = 10) -> list[dict]:
        """시트 미리보기"""
        pass

    async def get_sync_status(self) -> dict[str, SyncStatus]:
        """동기화 상태 조회"""
        pass
```

### 6.2 이벤트 발행

```python
# 동기화 완료
await self.emit(EventType.SHEETS_SYNC_COMPLETED, {
    "sheet_id": sheet_id,
    "rows_synced": 50,
    "clips_created": 45,
    "clips_updated": 5,
    "errors": 0,
    "duration_seconds": 30,
})

# 행 변경 감지
await self.emit(EventType.SHEETS_ROW_CHANGED, {
    "sheet_id": sheet_id,
    "row_number": 42,
    "change_type": "insert",  # insert, update, delete
    "data": {...},
})
```

---

## 7. 데이터 모델

### 7.1 GoogleSheetSync

```python
class GoogleSheetSync(Base, TimestampMixin):
    __tablename__ = "google_sheet_sync"
    __table_args__ = (
        UniqueConstraint("sheet_id", "entity_type"),
        {"schema": "pokervod"}
    )

    id: Mapped[UUID]
    sheet_id: Mapped[str]           # Google Sheet ID
    entity_type: Mapped[str]        # hand_clip, player, tag
    last_row_synced: Mapped[int] = 0
    last_synced_at: Mapped[datetime | None]
    sync_status: Mapped[str] = "idle"  # idle, syncing, completed, failed
    error_message: Mapped[str | None]
```

---

## 8. 에러 처리

### 8.1 API 속도 제한

```python
class RateLimitHandler:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.request_times: list[datetime] = []

    async def wait_if_needed(self):
        """속도 제한 대기"""
        now = datetime.utcnow()
        # 1분 이내 요청 필터
        self.request_times = [
            t for t in self.request_times
            if (now - t).seconds < 60
        ]

        if len(self.request_times) >= self.rpm:
            wait_time = 60 - (now - self.request_times[0]).seconds
            await asyncio.sleep(wait_time)

        self.request_times.append(now)
```

### 8.2 매칭 실패 처리

```python
async def process_row(self, row: dict) -> ProcessResult:
    """행 처리"""
    try:
        # 1. file_path 매칭 시도
        video_file = await self.match_file_path(row.get("nas_folder_link"))

        if not video_file:
            # 매칭 실패 로깅 (나중에 재시도)
            await self.log_unmatched(row, reason="file_path_not_found")
            return ProcessResult(status="unmatched", row=row)

        # 2. 클립 생성
        clip = await self.hand_analysis_agent.create_hand_clip(
            video_file_id=video_file.id,
            timecode=row.get("in"),
            timecode_end=row.get("out"),
            # ...
        )

        return ProcessResult(status="success", clip_id=clip.id)

    except Exception as e:
        await self.log_error(row, error=str(e))
        return ProcessResult(status="error", error=str(e))
```

---

## 9. 성능 요구사항

| 지표 | 목표 |
|------|------|
| 증분 동기화 지연 | < 60초 |
| 전체 동기화 (2,500행) | < 5분 |
| file_path 매칭 정확도 | 100% |
| 데이터 정합성 | 100% |
| API 에러율 | < 1% |

---

## 10. 테스트 케이스

### 10.1 매칭 테스트

```python
async def test_file_path_matching():
    agent = SheetsSyncAgent()

    # 정확한 경로
    result = await agent.match_file_path(
        "\\\\10.10.100.122\\docker\\GGPNAs\\ARCHIVE\\WSOP\\2024\\test.mp4"
    )
    assert result is not None

    # 정규화 필요
    result = await agent.match_file_path(
        "//10.10.100.122/docker/GGPNAs/ARCHIVE/WSOP/2024/test.mp4"
    )
    assert result is not None
```

### 10.2 정규화 테스트

```python
def test_split_multi_value():
    result = split_multi_value("Phil Hellmuth, Daniel Negreanu")
    assert result == ["Phil Hellmuth", "Daniel Negreanu"]

    result = split_multi_value("Cooler; Bluff | Hero Call")
    assert result == ["Cooler", "Bluff", "Hero Call"]
```

---

## 11. 의존성

### 11.1 외부 의존성

| 블럭 | 제공 데이터 |
|------|-----------|
| A (NAS) | `file_path` 매칭용 VideoFile |
| B (Catalog) | `title` 매칭용 Episode |

### 11.2 호출 대상

| 블럭 | 호출 내용 |
|------|---------|
| C (Hand Analysis) | `create_hand_clip()`, `add_tags()`, `link_players()` |

### 11.3 제공 데이터

| 소비자 블럭 | 제공 데이터 |
|------------|-----------|
| E (API) | 동기화 상태, 시트 미리보기 |

---

**문서 버전**: 1.0.0
**작성일**: 2025-12-11
