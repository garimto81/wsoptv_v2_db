# PRD: 블럭 B - Catalog Agent

> **버전**: 1.1.0 | **작성일**: 2025-12-11 | **블럭 코드**: B

---

## 1. 개요

### 1.1 목적

포커 콘텐츠의 계층 구조(Project → Season → Event → Episode)를 정의하고 관리합니다.

### 1.2 책임 범위

| 항목 | 포함 | 제외 |
|------|------|------|
| 프로젝트 등록 (7개) | O | |
| 시즌 관리 | O | |
| 이벤트 정의 | O | |
| 에피소드 생성 | O | |
| NAS SMB 스캔 | O | |
| NAS → DB 동기화 | O | |
| 핸드 분석 | | X (블럭 C) |

---

## 2. 카탈로그 계층 구조

### 2.1 ERD

```
Project (7개)
    │
    └─1:N─▶ Season (연도/시즌별)
                │
                └─1:N─▶ Event (토너먼트/이벤트)
                            │
                            └─1:N─▶ Episode (영상 단위)
                                        │
                                        └─1:N─▶ VideoFile
                                                    │
                                                    └─1:1─▶ NASFile
```

### 2.2 예시

```
WSOP (Project)
├── 2024 Las Vegas (Season)
│   ├── Event #21 - $25K NLH High Roller (Event)
│   │   ├── Final Table (Episode)
│   │   │   ├── 10-wsop-2024-be-ev-21-25k-nlh-hr-ft.mp4 (VideoFile - Mastered)
│   │   │   └── 10-wsop-2024-be-ev-21-25k-nlh-hr-ft-clean.mp4 (VideoFile - Clean)
│   │   └── Day 2 (Episode)
│   └── Event #12 - $1,500 6-MAX (Event)
└── 2023 Europe (Season)
```

---

## 3. 프로젝트 정의 (7개)

| Code | Name | Description | NAS Path |
|------|------|-------------|----------|
| `WSOP` | World Series of Poker | 브레이슬릿/서킷, 아카이브(1973~) | `/WSOP/` |
| `HCL` | Hustler Casino Live | 캐시게임, 하이라이트 | `/HCL/` |
| `GGMILLIONS` | GGMillions Super High Roller | 파이널 테이블 | `/GGMillions/` |
| `MPP` | Mediterranean Poker Party | 토너먼트 | `/MPP/` |
| `PAD` | Poker After Dark | TV 시리즈 (S12, S13) | `/PAD/` |
| `GOG` | Game of Gold | 에피소드 시리즈 | `/GOG 최종/` |
| `OTHER` | Other Projects | 기타 콘텐츠 | - |

---

## 4. 서브 카테고리

### 4.1 WSOP Sub-Categories

| Code | Description | 연도 범위 |
|------|-------------|----------|
| `ARCHIVE` | 1973-2016 역사 아카이브 | 1973-2016 |
| `BRACELET_LV` | Las Vegas 브레이슬릿 | 2017+ |
| `BRACELET_EU` | Europe 브레이슬릿 | 2017+ |
| `BRACELET_PARA` | Paradise 브레이슬릿 | 2023+ |
| `CIRCUIT` | 서킷 이벤트 | 2017+ |
| `SUPER_CIRCUIT` | 슈퍼 서킷 | 2020+ |

### 4.2 이벤트 타입

| Type | Description |
|------|-------------|
| `bracelet` | 브레이슬릿 이벤트 |
| `circuit` | 서킷 이벤트 |
| `super_circuit` | 슈퍼 서킷 |
| `high_roller` | 하이롤러 |
| `super_high_roller` | 슈퍼 하이롤러 |
| `cash_game` | 캐시게임 |
| `tv_series` | TV 시리즈 |
| `mystery_bounty` | 미스터리 바운티 |
| `main_event` | 메인 이벤트 |

### 4.3 게임 타입

| Type | Description |
|------|-------------|
| `NLHE` | No Limit Hold'em |
| `PLO` | Pot Limit Omaha |
| `PLO8` | Pot Limit Omaha Hi-Lo |
| `Mixed` | 믹스드 게임 |
| `Stud` | 스터드 |
| `Razz` | 라즈 |
| `HORSE` | H.O.R.S.E. |
| `2-7TD` | 2-7 Triple Draw |

---

## 5. NAS 연동 (구현 완료)

### 5.1 NAS 설정

```python
# backend/src/config.py
class NASConfig(BaseSettings):
    nas_host: str = "10.10.100.122"
    nas_share: str = "docker"
    nas_base_path: str = "GGPNAs"
    nas_username: str = "GGP"
    nas_password: str = "!@QW12qw"
    nas_port: int = 445
    nas_timeout: int = 30
```

### 5.2 SMB Scanner

```python
# backend/src/services/nas_inventory/smb_scanner.py
class SMBScanner:
    """SMB Protocol Scanner for NAS.

    Features:
    - SMB2/SMB3 지원 (smbprotocol 라이브러리)
    - Async/await 패턴 (thread pool executor)
    - 재귀적 폴더 스캔
    - 파일 메타데이터 추출
    """

    async def scan_directory(
        self,
        path: str = "",
        recursive: bool = False,
        max_depth: int = 10,
    ) -> AsyncGenerator[ScanResult, None]:
        """Scan a directory and yield results."""
        pass

    async def get_file_info(self, path: str) -> Optional[ScanResult]:
        """Get info for a specific file or directory."""
        pass
```

### 5.3 동기화 서비스

```python
# backend/src/services/nas_inventory/sync_service.py
class NASSyncService:
    """NAS Synchronization Service.

    Features:
    - NAS 스캔 결과 → PostgreSQL DB 동기화
    - 프로젝트별 동기화 지원
    - 파일 카테고리 자동 분류 (video, metadata, archive)
    - 증분 동기화 (변경 파일만 업데이트)
    """

    async def sync_all(self, max_depth: int = 5) -> SyncStats:
        """Sync entire NAS base path."""
        pass

    async def sync_project(self, project_code: str, max_depth: int = 5) -> SyncStats:
        """Sync a specific project folder."""
        pass
```

### 5.4 REST API 엔드포인트

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/nas/connection-test` | GET | NAS 연결 테스트 |
| `/api/v1/nas/scan` | POST | NAS 폴더 스캔 (DB 저장 없음) |
| `/api/v1/nas/sync` | POST | NAS → DB 동기화 |
| `/api/v1/nas/folders` | GET | 폴더 목록 조회 |
| `/api/v1/nas/folders/root` | GET | 루트 폴더 목록 |
| `/api/v1/nas/files` | GET | 파일 목록 조회 |
| `/api/v1/nas/files/videos` | GET | 비디오 파일 목록 |
| `/api/v1/nas/files/stats` | GET | 파일 통계 |

---

## 6. API

### 6.1 에이전트 인터페이스

```python
class CatalogAgent(BaseAgent):
    block_id = "B"

    async def create_project(self, code: str, name: str, **kwargs) -> Project:
        """프로젝트 생성"""
        pass

    async def add_season(
        self,
        project_id: UUID,
        year: int,
        name: str,
        location: str | None = None,
        sub_category: str | None = None,
    ) -> Season:
        """시즌 추가"""
        pass

    async def add_event(
        self,
        season_id: UUID,
        name: str,
        event_number: int | None = None,
        event_type: str | None = None,
        game_type: str | None = None,
        buy_in: Decimal | None = None,
    ) -> Event:
        """이벤트 추가"""
        pass

    async def create_episode(
        self,
        event_id: UUID,
        title: str | None = None,
        episode_number: int | None = None,
        day_number: int | None = None,
        episode_type: str | None = None,
        table_type: str | None = None,
    ) -> Episode:
        """에피소드 생성"""
        pass

    async def match_episode(self, file_name: str, parsed_metadata: dict) -> Episode | None:
        """파일명으로 에피소드 매칭"""
        pass

    async def get_catalog_tree(self, project_code: str | None = None) -> CatalogTree:
        """카탈로그 트리 조회"""
        pass
```

### 6.2 이벤트 발행

```python
# 카탈로그 업데이트 완료
await self.emit(EventType.CATALOG_UPDATED, {
    "projects": 7,
    "seasons": 45,
    "events": 320,
    "episodes": 1400,
})

# 에피소드 생성
await self.emit(EventType.EPISODE_CREATED, {
    "episode_id": str(episode.id),
    "event_id": str(event.id),
    "title": episode.title,
})
```

---

## 7. 데이터 모델

### 7.1 Project

```python
class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[UUID]
    code: Mapped[str]               # unique, WSOP, HCL, etc.
    name: Mapped[str]
    description: Mapped[str | None]
    nas_base_path: Mapped[str | None]
    filename_pattern: Mapped[str | None]  # 파싱 패턴 정규식
    is_active: Mapped[bool] = True

    seasons: Mapped[list["Season"]] = relationship(back_populates="project")
```

### 7.2 Season

```python
class Season(Base, TimestampMixin):
    __tablename__ = "seasons"

    id: Mapped[UUID]
    project_id: Mapped[UUID]        # FK → Project
    year: Mapped[int]
    name: Mapped[str]
    location: Mapped[str | None]    # LAS VEGAS, EUROPE, etc.
    sub_category: Mapped[str | None]  # ARCHIVE, BRACELET_LV, etc.
    status: Mapped[str] = "active"

    project: Mapped["Project"] = relationship(back_populates="seasons")
    events: Mapped[list["Event"]] = relationship(back_populates="season")
```

### 7.3 Event

```python
class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[UUID]
    season_id: Mapped[UUID]         # FK → Season
    event_number: Mapped[int | None]
    name: Mapped[str]
    name_short: Mapped[str | None]  # 축약 이름
    event_type: Mapped[str | None]  # bracelet, circuit, etc.
    game_type: Mapped[str | None]   # NLHE, PLO, etc.
    buy_in: Mapped[Decimal | None]
    gtd_amount: Mapped[Decimal | None]
    venue: Mapped[str | None]
    status: Mapped[str] = "upcoming"

    season: Mapped["Season"] = relationship(back_populates="events")
    episodes: Mapped[list["Episode"]] = relationship(back_populates="event")
```

### 7.4 Episode

```python
class Episode(Base, TimestampMixin):
    __tablename__ = "episodes"

    id: Mapped[UUID]
    event_id: Mapped[UUID]          # FK → Event
    episode_number: Mapped[int | None]
    day_number: Mapped[int | None]
    part_number: Mapped[int | None]
    title: Mapped[str | None]
    episode_type: Mapped[str | None]  # full, highlight, recap, interview, subclip
    table_type: Mapped[str | None]    # preliminary, day1, day2, final_table, heads_up
    duration_seconds: Mapped[int | None]

    event: Mapped["Event"] = relationship(back_populates="episodes")
    video_files: Mapped[list["VideoFile"]] = relationship(back_populates="episode")
    hand_clips: Mapped[list["HandClip"]] = relationship(back_populates="episode")
```

### 7.5 NASFolder (구현 완료)

```python
class NASFolder(Base, TimestampMixin):
    __tablename__ = "nas_folders"

    id: Mapped[UUID]
    folder_path: Mapped[str]        # unique, indexed
    folder_name: Mapped[str]
    parent_path: Mapped[str | None]
    depth: Mapped[int] = 0

    # Statistics
    file_count: Mapped[int] = 0
    folder_count: Mapped[int] = 0
    total_size_bytes: Mapped[int] = 0

    # Metadata
    is_empty: Mapped[bool] = True
    is_hidden_folder: Mapped[bool] = False

    files: Mapped[list["NASFile"]] = relationship(back_populates="folder")
```

### 7.6 NASFile (구현 완료)

```python
class NASFile(Base, TimestampMixin):
    __tablename__ = "nas_files"

    id: Mapped[UUID]
    file_path: Mapped[str]          # unique, indexed
    file_name: Mapped[str]
    file_size_bytes: Mapped[int] = 0
    file_extension: Mapped[str | None]
    file_mtime: Mapped[datetime | None]

    # Classification
    file_category: Mapped[str] = "other"  # video, metadata, system, archive, other
    is_hidden_file: Mapped[bool] = False

    # Foreign keys
    video_file_id: Mapped[UUID | None]  # FK → VideoFile
    folder_id: Mapped[UUID | None]      # FK → NASFolder

    video_file: Mapped["VideoFile" | None] = relationship(back_populates="nas_file")
    folder: Mapped["NASFolder" | None] = relationship(back_populates="files")
```

---

## 8. 매칭 알고리즘

### 8.1 에피소드 매칭 흐름

```python
async def match_episode(self, file_name: str, parsed_metadata: dict) -> Episode | None:
    """
    1. project_code → Project 찾기
    2. year + location → Season 찾기
    3. event_number/name → Event 찾기
    4. day/table_type → Episode 찾기 (없으면 생성)
    """
    project = await self._find_project(parsed_metadata.get("project_code"))
    if not project:
        return None

    season = await self._find_or_create_season(
        project.id,
        parsed_metadata.get("year"),
        parsed_metadata.get("location"),
    )

    event = await self._find_or_create_event(
        season.id,
        parsed_metadata.get("event_number"),
        parsed_metadata.get("event_name"),
        parsed_metadata.get("game_type"),
        parsed_metadata.get("buy_in"),
    )

    episode = await self._find_or_create_episode(
        event.id,
        parsed_metadata.get("day_number"),
        parsed_metadata.get("table_type"),
        parsed_metadata.get("episode_title"),
    )

    return episode
```

### 8.2 자동 생성 규칙

| 엔티티 | 자동 생성 조건 |
|--------|---------------|
| Project | 절대 자동 생성 안함 (7개 고정) |
| Season | 새로운 year+location 조합 발견 시 |
| Event | 새로운 event_number 발견 시 |
| Episode | 새로운 day/table_type 발견 시 |

---

## 9. 성능 요구사항

| 지표 | 목표 |
|------|------|
| 전체 카탈로그 로드 | < 100ms |
| 단일 에피소드 매칭 | < 50ms |
| 트리 쿼리 | < 200ms |
| 캐시 히트율 | > 90% |
| NAS 스캔 (1000 파일) | < 30s |
| NAS → DB 동기화 | < 60s |

---

## 10. 테스트 케이스

### 10.1 매칭 테스트

```python
async def test_match_wsop_episode():
    agent = CatalogAgent()
    parsed = {
        "project_code": "WSOP",
        "year": 2024,
        "location": "LAS VEGAS",
        "event_number": 21,
        "game_type": "NLHE",
        "buy_in": 25000,
        "table_type": "final_table",
    }

    episode = await agent.match_episode("test.mp4", parsed)

    assert episode is not None
    assert episode.event.event_number == 21
    assert episode.table_type == "final_table"
```

### 10.2 트리 테스트

```python
async def test_catalog_tree():
    agent = CatalogAgent()
    tree = await agent.get_catalog_tree("WSOP")

    assert tree.project.code == "WSOP"
    assert len(tree.seasons) > 0
```

### 10.3 NAS 연결 테스트

```python
async def test_nas_connection():
    scanner = SMBScanner()
    await scanner.connect()

    assert scanner._connected

    await scanner.disconnect()
```

### 10.4 NAS 스캔 테스트

```python
async def test_nas_scan():
    async with SMBScanner() as scanner:
        items = []
        async for result in scanner.scan_directory("WSOP", recursive=False):
            items.append(result)

        assert len(items) > 0
```

---

## 11. 의존성

### 11.1 외부 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `smbprotocol` | >= 1.13.0 | SMB/CIFS 프로토콜 |
| `sqlalchemy` | >= 2.0.25 | ORM |
| `asyncpg` | >= 0.29.0 | PostgreSQL async driver |

### 11.2 제공 데이터

| 소비자 블럭 | 제공 데이터 |
|------------|-----------|
| C (Hand Analysis) | `Episode` 참조 |
| D (Sheets Sync) | `Episode` 매칭 |
| E (API) | 카탈로그 트리, 프로젝트 목록 |
| Frontend | NAS 파일 목록, 스캔 결과 |

---

## 12. 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│                     localhost:3000                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   wsoptv_v2_db API (FastAPI)                    │
│                     localhost:8000                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Catalog API │  │   NAS API   │  │  Hand Analysis API      │ │
│  └─────────────┘  └──────┬──────┘  └─────────────────────────┘ │
└──────────────────────────┼──────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌────────────┐          ┌────────────────────┐
       │ PostgreSQL │          │ NAS (SMB)          │
       │ pokervod   │          │ \\10.10.100.122    │
       └────────────┘          │ \docker\GGPNAs     │
                               └────────────────────┘
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2025-12-11 | 초기 작성 |
| 1.1.0 | 2025-12-11 | NAS SMB 스캔/동기화 구현 추가 |

---

**문서 버전**: 1.1.0
**작성일**: 2025-12-11
