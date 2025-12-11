# PRD: 블럭 E - API Agent

> **버전**: 1.0.0 | **작성일**: 2025-12-11 | **블럭 코드**: E

---

## 1. 개요

### 1.1 목적

PokerVOD 시스템의 REST API를 제공합니다. 프론트엔드 및 외부 시스템이 데이터를 조회하고 동기화를 트리거할 수 있습니다.

### 1.2 책임 범위

| 항목 | 포함 | 제외 |
|------|------|------|
| REST 엔드포인트 | O | |
| 캐싱 | O | |
| 페이지네이션 | O | |
| 인증/인가 | O | |
| 비즈니스 로직 | | X (각 블럭) |
| 데이터 수정 | | X (읽기 전용) |

---

## 2. 엔드포인트 구조

### 2.1 베이스 URL

```
http://localhost:9000/api/v1
```

### 2.2 엔드포인트 목록

| 그룹 | 엔드포인트 | 메서드 | 설명 |
|------|-----------|--------|------|
| **Projects** | `/projects` | GET | 프로젝트 목록 |
| | `/projects/{id}` | GET | 프로젝트 상세 |
| | `/projects/{id}/seasons` | GET | 프로젝트의 시즌 목록 |
| **Seasons** | `/seasons` | GET | 시즌 목록 (필터링) |
| | `/seasons/{id}` | GET | 시즌 상세 |
| | `/seasons/{id}/events` | GET | 시즌의 이벤트 목록 |
| **Events** | `/events` | GET | 이벤트 목록 |
| | `/events/{id}` | GET | 이벤트 상세 |
| | `/events/{id}/episodes` | GET | 이벤트의 에피소드 목록 |
| **Episodes** | `/episodes` | GET | 에피소드 목록 |
| | `/episodes/{id}` | GET | 에피소드 상세 |
| | `/episodes/{id}/videos` | GET | 에피소드의 비디오 목록 |
| | `/episodes/{id}/clips` | GET | 에피소드의 핸드 클립 목록 |
| **Catalog** | `/catalog` | GET | 카탈로그 아이템 |
| | `/catalog/search` | GET | 카탈로그 검색 |
| | `/catalog/stats` | GET | 카탈로그 통계 |
| | `/catalog/filters` | GET | 필터 옵션 |
| **Hand Clips** | `/clips` | GET | 핸드 클립 목록 |
| | `/clips/{id}` | GET | 클립 상세 |
| | `/clips/search` | GET | 클립 검색 |
| **Tags** | `/tags` | GET | 태그 목록 |
| | `/tags/categories` | GET | 태그 카테고리 |
| **Players** | `/players` | GET | 플레이어 목록 |
| | `/players/{id}` | GET | 플레이어 상세 |
| | `/players/{id}/clips` | GET | 플레이어의 클립 목록 |
| **Sync** | `/sync/status` | GET | 동기화 상태 |
| | `/sync/trigger/{source}` | POST | 동기화 트리거 |
| | `/sync/tree` | GET | NAS 폴더 트리 |
| | `/sync/sheets/preview` | GET | Sheets 미리보기 |
| **Health** | `/health` | GET | 헬스 체크 |
| | `/health/db` | GET | DB 상태 |
| | `/health/nas` | GET | NAS 연결 상태 |

---

## 3. API 명세

### 3.1 프로젝트 API

#### GET /projects

```python
@router.get("/projects")
async def list_projects(
    is_active: bool | None = None,
) -> list[ProjectResponse]:
    """프로젝트 목록 조회"""
    pass

# Response
class ProjectResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    season_count: int
    video_count: int
```

#### GET /projects/{id}

```python
@router.get("/projects/{id}")
async def get_project(id: UUID) -> ProjectDetailResponse:
    """프로젝트 상세 조회"""
    pass

# Response
class ProjectDetailResponse(ProjectResponse):
    nas_base_path: str | None
    seasons: list[SeasonSummary]
    stats: ProjectStats
```

### 3.2 카탈로그 API

#### GET /catalog

```python
@router.get("/catalog")
async def list_catalog(
    project: str | None = None,
    year: int | None = None,
    game_type: str | None = None,
    version_type: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> PaginatedResponse[CatalogItem]:
    """카탈로그 아이템 목록"""
    pass

# Response
class CatalogItem(BaseModel):
    id: UUID
    title: str
    project_code: str
    season_year: int
    event_name: str
    episode_type: str
    version_type: str
    duration_seconds: int | None
    thumbnail_url: str | None
```

#### GET /catalog/search

```python
@router.get("/catalog/search")
async def search_catalog(
    q: str,  # 검색어
    project: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    page: int = 1,
    limit: int = 20,
) -> PaginatedResponse[CatalogItem]:
    """카탈로그 검색"""
    pass
```

#### GET /catalog/stats

```python
@router.get("/catalog/stats")
async def get_catalog_stats() -> CatalogStats:
    """카탈로그 통계"""
    pass

# Response
class CatalogStats(BaseModel):
    total_projects: int
    total_seasons: int
    total_events: int
    total_episodes: int
    total_videos: int
    total_size_tb: float
    by_project: dict[str, int]  # {WSOP: 1279, PAD: 45, ...}
    by_year: dict[int, int]     # {2024: 500, 2023: 400, ...}
```

### 3.3 핸드 클립 API

#### GET /clips

```python
@router.get("/clips")
async def list_clips(
    project: str | None = None,
    player: str | None = None,
    tags: list[str] | None = Query(None),
    hand_grade: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> PaginatedResponse[ClipResponse]:
    """핸드 클립 목록"""
    pass

# Response
class ClipResponse(BaseModel):
    id: UUID
    title: str | None
    timecode: str
    timecode_end: str
    duration_seconds: int
    hand_grade: str | None
    winner_hand: str | None
    tags: list[TagSummary]
    players: list[PlayerSummary]
    video_file: VideoFileSummary | None
```

#### GET /clips/search

```python
@router.get("/clips/search")
async def search_clips(
    q: str | None = None,
    tags: list[str] | None = Query(None),
    players: list[str] | None = Query(None),
    hand_grade: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> PaginatedResponse[ClipResponse]:
    """클립 검색 (다중 필터)"""
    pass
```

### 3.4 동기화 API

#### GET /sync/status

```python
@router.get("/sync/status")
async def get_sync_status() -> SyncStatusResponse:
    """동기화 상태 조회"""
    pass

# Response
class SyncStatusResponse(BaseModel):
    overall: str  # idle, syncing, completed, failed
    blocks: dict[str, BlockStatus]
    last_full_sync: datetime | None
    next_scheduled_sync: datetime | None

class BlockStatus(BaseModel):
    block_id: str
    status: str
    last_sync_at: datetime | None
    items_processed: int
    items_total: int
    error_message: str | None
```

#### POST /sync/trigger/{source}

```python
@router.post("/sync/trigger/{source}")
async def trigger_sync(
    source: str,  # nas, sheets, all
    sync_type: str = "incremental",  # incremental, full
) -> SyncTriggerResponse:
    """동기화 트리거"""
    pass

# Response
class SyncTriggerResponse(BaseModel):
    task_id: str
    status: str  # started, queued
    estimated_duration: int | None
```

---

## 4. 공통 응답 구조

### 4.1 페이지네이션

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool
```

### 4.2 에러 응답

```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict | None = None
    timestamp: datetime

# HTTP 상태 코드
# 400 - Bad Request (잘못된 파라미터)
# 404 - Not Found (리소스 없음)
# 500 - Internal Server Error (서버 오류)
# 503 - Service Unavailable (동기화 중)
```

---

## 5. 캐싱 전략

### 5.1 캐시 레이어

```python
from functools import lru_cache
from cachetools import TTLCache

# 메모리 캐시
CACHE_CONFIG = {
    "projects": TTLCache(maxsize=100, ttl=3600),      # 1시간
    "catalog_stats": TTLCache(maxsize=1, ttl=300),   # 5분
    "filters": TTLCache(maxsize=1, ttl=600),         # 10분
    "sync_status": TTLCache(maxsize=1, ttl=30),      # 30초
}
```

### 5.2 캐시 무효화

```python
class CacheInvalidator:
    async def on_event(self, event: Event):
        if event.type == EventType.CATALOG_UPDATED:
            CACHE_CONFIG["projects"].clear()
            CACHE_CONFIG["catalog_stats"].clear()
            CACHE_CONFIG["filters"].clear()

        if event.type == EventType.SYNC_ALL_COMPLETED:
            # 모든 캐시 무효화
            for cache in CACHE_CONFIG.values():
                cache.clear()
```

---

## 6. 인증/인가

### 6.1 API 키 인증 (선택)

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

### 6.2 CORS 설정

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # 프론트엔드
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 7. API 인터페이스

### 7.1 에이전트 인터페이스

```python
class APIAgent(BaseAgent):
    block_id = "E"

    # 프로젝트
    async def list_projects(self, **filters) -> list[ProjectResponse]:
        pass

    async def get_project(self, id: UUID) -> ProjectDetailResponse:
        pass

    # 카탈로그
    async def search_catalog(self, query: str, **filters) -> list[CatalogItem]:
        pass

    async def get_statistics(self) -> CatalogStats:
        pass

    # 클립
    async def search_clips(self, **filters) -> list[ClipResponse]:
        pass

    # 동기화
    async def get_sync_status(self) -> SyncStatusResponse:
        pass

    async def trigger_sync(self, source: str, sync_type: str) -> str:
        pass

    # 캐시
    async def refresh_cache(self):
        pass
```

---

## 8. 성능 요구사항

| 엔드포인트 | 목표 (p95) |
|-----------|-----------|
| `/projects` | < 50ms |
| `/catalog` | < 100ms |
| `/catalog/search` | < 200ms |
| `/clips/search` | < 200ms |
| `/sync/status` | < 50ms |
| `/catalog/stats` | < 100ms |

### 8.1 최적화 전략

```python
# 1. 인덱스 활용
# - projects(code)
# - seasons(project_id, year)
# - events(season_id, event_number)
# - hand_clips(video_file_id)
# - tags(category, name)

# 2. Eager Loading
query = select(Project).options(
    selectinload(Project.seasons).selectinload(Season.events)
)

# 3. 결과 제한
query = query.limit(100)  # 최대 100개
```

---

## 9. 테스트 케이스

### 9.1 API 테스트

```python
from fastapi.testclient import TestClient

def test_list_projects(client: TestClient):
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7  # 7개 프로젝트

def test_search_clips(client: TestClient):
    response = client.get("/api/v1/clips/search", params={
        "tags": ["cooler", "bluff"],
        "hand_grade": "★★★",
    })
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
```

### 9.2 성능 테스트

```python
import pytest
from time import time

@pytest.mark.benchmark
def test_catalog_search_performance(client: TestClient):
    start = time()
    response = client.get("/api/v1/catalog/search", params={"q": "wsop 2024"})
    elapsed = time() - start

    assert response.status_code == 200
    assert elapsed < 0.2  # 200ms 이내
```

---

## 10. 의존성

### 10.1 외부 의존성

| 블럭 | 제공 데이터 |
|------|-----------|
| A (NAS) | NAS 트리, 파일 목록 |
| B (Catalog) | 프로젝트/시즌/이벤트/에피소드 |
| C (Hand Analysis) | 클립, 태그, 플레이어 |
| D (Sheets Sync) | 동기화 상태 |

### 10.2 제공 데이터

| 소비자 블럭 | 제공 데이터 |
|------------|-----------|
| F (Dashboard) | 모든 REST API |

---

**문서 버전**: 1.0.0
**작성일**: 2025-12-11
