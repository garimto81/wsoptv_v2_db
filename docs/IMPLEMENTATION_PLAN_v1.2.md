# Implementation Plan v1.2.0 - 데이터 매칭 검증 시스템

> **작성일**: 2025-12-11 | **PRD 버전**: 1.2.0 | **상태**: 승인 대기

---

## 1. 현재 상태 분석

### 1.1 발견된 문제점

| # | 문제 | 현황 | 영향도 |
|---|------|------|--------|
| 1 | **제목 자동 생성 미작동** | VideoFile 1,263개 중 display_title = 0개 | Critical |
| 2 | **Google Sheets 동기화 미작동** | HandClip = 0개 (시트 데이터 없음) | Critical |
| 3 | **NAS ↔ Sheets 매칭 불가** | 위 문제로 검증 불가 | Blocked |

### 1.2 현재 데이터 흐름

```
NAS Files (1,429개)
    ↓ [파싱 O]
ParsedMetadata (메타데이터 추출됨)
    ↓ [제목 생성 X] ← 문제 1
VideoFile (1,263개, display_title=NULL)
    ↓ [매칭 불가]
Google Sheets (2,500+ 행)
    ↓ [동기화 X] ← 문제 2
HandClip (0개)
```

### 1.3 기존 코드 분석

| 컴포넌트 | 파일 | 상태 |
|----------|------|------|
| 파서 | `file_parser/*.py` | 7개 파서 구현됨 (제목 생성 없음) |
| CatalogBuilder | `catalog_builder_service.py` | VideoFile 생성 (제목 미생성) |
| Sheets Service | `sheets_service.py` | 구현 필요 |
| HandClip Service | `hand_clip_service.py` | 기본 CRUD만 있음 |

---

## 2. 구현 계획 개요

### 2.1 Phase 구성

| Phase | 작업 | 예상 파일 수정 | 의존성 |
|-------|------|--------------|--------|
| **Phase 1** | 제목 자동 생성 로직 | 3개 | 없음 |
| **Phase 2** | Google Sheets 동기화 | 4개 | Phase 1 |
| **Phase 3** | NAS ↔ Sheets 매칭 | 2개 | Phase 2 |
| **Phase 4** | Validation API + UI | 4개 | Phase 3 |

### 2.2 전체 흐름 (목표)

```
NAS Files (1,429개)
    ↓ [파싱]
ParsedMetadata
    ↓ [제목 생성기] ← Phase 1
VideoFile (display_title, catalog_title 포함)
    ↓
Google Sheets (2,500+ 행)
    ↓ [Sheets 동기화] ← Phase 2
HandClip (video_file_id 설정됨)
    ↓ [경로 매칭] ← Phase 3
NASFile ↔ VideoFile ↔ HandClip 연결 완료
    ↓
Validation API + Dashboard ← Phase 4
```

---

## 3. Phase 1: 제목 자동 생성

### 3.1 목표

- ParsedMetadata → display_title, catalog_title 변환
- 기존 VideoFile에 제목 일괄 업데이트

### 3.2 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `services/file_parser/title_generator.py` | **신규** - 제목 생성 로직 |
| `services/file_parser/base_parser.py` | display_title, catalog_title 필드 활용 |
| `services/catalog/catalog_builder_service.py` | 제목 생성 호출 추가 |

### 3.3 title_generator.py 설계

```python
# backend/src/services/file_parser/title_generator.py

class TitleGenerator:
    """ParsedMetadata에서 display_title, catalog_title 생성."""

    PROJECT_NAMES = {
        "WSOP": "WSOP",
        "WSOP_CIRCUIT": "WSOP Circuit",
        "GGMILLIONS": "GG Millions",
        "GOG": "Game of Gold",
        "PAD": "Poker After Dark",
        "MPP": "MPP",
        "HCL": "Hustler Casino Live",
    }

    TABLE_TYPE_NAMES = {
        "final_table": "Final Table",
        "ft": "Final Table",
        "heads_up": "Heads Up",
        "hu": "Heads Up",
        "day1": "Day 1",
        "day2": "Day 2",
        "day3": "Day 3",
        "d1": "Day 1",
        "d2": "Day 2",
        "d3": "Day 3",
    }

    GAME_TYPE_NAMES = {
        "NLHE": "No Limit Hold'em",
        "NLH": "No Limit Hold'em",
        "PLO": "Pot Limit Omaha",
        "PLO8": "PLO Hi-Lo",
    }

    def generate(self, metadata: ParsedMetadata) -> tuple[str, str]:
        """display_title과 catalog_title 생성.

        Returns:
            (display_title, catalog_title) 튜플
        """
        display_title = self._generate_display_title(metadata)
        catalog_title = self._generate_catalog_title(metadata)
        return display_title, catalog_title

    def _generate_display_title(self, m: ParsedMetadata) -> str:
        """전체 제목 생성."""
        parts = []

        # 1. 프로젝트명
        project_name = self.PROJECT_NAMES.get(m.project_code, m.project_code or "")
        if project_name:
            parts.append(project_name)

        # 2. 연도
        if m.year:
            parts.append(str(m.year))

        # 3. 이벤트 정보
        if m.event_number:
            parts.append(f"Event #{m.event_number}")
        elif m.event_name:
            parts.append(m.event_name)

        # 4. 바이인
        if m.buy_in:
            buy_in = m.buy_in.upper()
            if not buy_in.startswith("$"):
                buy_in = f"${buy_in}"
            parts.append(buy_in)

        # 5. 게임 타입
        if m.game_type:
            parts.append(m.game_type)

        # 6. 테이블/데이 정보
        if m.table_type:
            table_name = self.TABLE_TYPE_NAMES.get(m.table_type, m.table_type)
            parts.append(table_name)
        elif m.day_info:
            parts.append(m.day_info)

        # 7. 에피소드
        if m.episode_number and m.project_code in ("GOG", "PAD"):
            parts.append(f"Episode {m.episode_number}")

        # 8. 시즌 (PAD)
        if m.season_number and m.project_code == "PAD":
            # 앞에 시즌 정보 삽입
            parts.insert(1, f"S{m.season_number}")

        # 9. 피처드 플레이어 (GGMillions)
        if m.featured_player:
            parts.append(f"ft. {m.featured_player}")

        # Fallback: 파일명 사용
        if not parts or len(parts) <= 1:
            return self._fallback_title(m)

        return " ".join(parts)

    def _generate_catalog_title(self, m: ParsedMetadata) -> str:
        """카드용 짧은 제목 생성."""
        parts = []

        # 프로젝트 약어
        project_abbrev = {
            "WSOP": "WSOP",
            "WSOP_CIRCUIT": "WSOP-C",
            "GGMILLIONS": "GGM",
            "GOG": "GOG",
            "PAD": "PAD",
            "MPP": "MPP",
            "HCL": "HCL",
        }
        abbrev = project_abbrev.get(m.project_code, m.project_code or "")
        if abbrev:
            parts.append(abbrev)

        # 연도 (마지막 2자리)
        if m.year:
            parts.append(f"'{str(m.year)[-2:]}")

        # 이벤트 번호 또는 에피소드
        if m.event_number:
            parts.append(f"#{m.event_number}")
        elif m.episode_number:
            parts.append(f"E{m.episode_number:02d}")

        # 테이블 타입 약어
        if m.table_type in ("final_table", "ft"):
            parts.append("FT")
        elif m.table_type in ("heads_up", "hu"):
            parts.append("HU")

        return " ".join(parts) if parts else m.raw_filename[:30]

    def _fallback_title(self, m: ParsedMetadata) -> str:
        """파싱 실패 시 파일명에서 제목 생성."""
        name = m.raw_filename
        # 확장자 제거
        if "." in name:
            name = name.rsplit(".", 1)[0]
        # 언더스코어/하이픈을 공백으로
        name = name.replace("_", " ").replace("-", " ")
        # 타이틀 케이스
        return name.title()[:100]
```

### 3.4 catalog_builder_service.py 수정

```python
# _create_video_file 메서드 수정

from ..file_parser.title_generator import TitleGenerator

class CatalogBuilderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.title_generator = TitleGenerator()
        # ... 기존 코드

    async def _create_video_file(self, nas_file, episode_id, metadata, stats):
        # 제목 생성 추가
        display_title, catalog_title = self.title_generator.generate(metadata)

        video_file = VideoFile(
            episode_id=episode_id,
            file_path=nas_file.file_path,
            file_name=nas_file.file_name,
            # ... 기존 필드
            display_title=display_title,      # 추가
            catalog_title=catalog_title,      # 추가
        )
```

### 3.5 기존 VideoFile 업데이트 API

```python
# POST /api/v1/quality/regenerate-titles
# 기존 VideoFile에 제목 일괄 재생성
```

---

## 4. Phase 2: Google Sheets 동기화

### 4.1 목표

- Google Sheets → HandClip 테이블 동기화
- Nas Folder Link 컬럼 저장

### 4.2 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `services/sync/sheets_sync_service.py` | **신규** - Sheets 동기화 로직 |
| `models/hand_clip.py` | nas_folder_link 컬럼 추가 |
| `api/v1/sync.py` | 동기화 트리거 API |

### 4.3 HandClip 모델 수정

```python
# models/hand_clip.py에 컬럼 추가

class HandClip(Base, TimestampMixin):
    # 기존 필드...

    # Sheets 원본 데이터 (매칭용)
    nas_folder_link: Mapped[Optional[str]] = mapped_column(String(1000))
    sheet_file_name: Mapped[Optional[str]] = mapped_column(String(500))
```

### 4.4 SheetsSyncService 설계

```python
# backend/src/services/sync/sheets_sync_service.py

class SheetsSyncService:
    """Google Sheets → HandClip 동기화."""

    SHEET_ID_METADATA = "1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4"
    SHEET_ID_ICONIK = "1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk"

    async def sync_metadata_archive(self) -> SyncResult:
        """metadata_archive 시트 동기화."""
        # 1. Google Sheets API로 데이터 가져오기
        # 2. 각 행을 HandClip으로 변환
        # 3. nas_folder_link 저장
        # 4. video_file_id는 Phase 3에서 매칭

    async def sync_iconik_metadata(self) -> SyncResult:
        """iconik_metadata 시트 동기화."""
        # UUID 기반 ID 활용
```

---

## 5. Phase 3: NAS ↔ Sheets 매칭

### 5.1 목표

- HandClip.nas_folder_link ↔ NASFile.file_path 매칭
- video_file_id 자동 설정

### 5.2 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `services/matching/path_matcher.py` | **신규** - 경로 매칭 로직 |
| `api/v1/quality.py` | 매칭 트리거 API |

### 5.3 PathMatcher 설계

```python
# backend/src/services/matching/path_matcher.py

class PathMatcher:
    """NAS 경로 ↔ Sheets 경로 매칭."""

    def normalize_path(self, path: str) -> str:
        """경로 정규화.

        Input:  \\\\10.10.100.122\\docker\\GGPNAs\\ARCHIVE\\WSOP\\file.mp4
        Output: ggpnas/archive/wsop/file.mp4
        """
        # 1. UNC 프리픽스 제거
        path = re.sub(r'^\\\\[^\\]+\\[^\\]+\\', '', path)
        # 2. 백슬래시 → 슬래시
        path = path.replace('\\', '/')
        # 3. 소문자 변환
        return path.lower()

    async def match_handclips_to_videofiles(self, session: AsyncSession) -> MatchResult:
        """HandClip의 nas_folder_link로 VideoFile 매칭."""
        # 1. 미연결 HandClip 조회
        # 2. nas_folder_link 정규화
        # 3. NASFile.file_path와 매칭
        # 4. NASFile.video_file_id로 연결
```

### 5.4 매칭 API

```python
# POST /api/v1/quality/match-handclips
# HandClip ↔ VideoFile 매칭 실행
```

---

## 6. Phase 4: Validation API + Dashboard

### 6.1 목표

- 제목 생성 검증 API
- NAS ↔ Sheets 매칭 검증 API
- 프론트엔드 검증 탭 추가

### 6.2 신규 API 엔드포인트

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/validation/title-samples` | 제목 변환 샘플 |
| `GET /api/v1/validation/matching-samples` | 매칭 샘플 |
| `GET /api/v1/validation/mismatches` | 매칭 실패 목록 |
| `GET /api/v1/validation/coverage` | 전체 커버리지 |

### 6.3 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `api/v1/validation.py` | **신규** - Validation API |
| `frontend/src/app/validation/page.tsx` | **신규** - 검증 대시보드 |
| `frontend/src/hooks/use-validation.ts` | **신규** - API 훅 |

### 6.4 validation.py 설계

```python
# backend/src/api/v1/validation.py

@router.get("/title-samples")
async def get_title_samples(
    limit: int = 20,
    parser: Optional[str] = None,
) -> TitleSamplesResponse:
    """제목 변환 샘플 조회.

    원본 파일명 → display_title → catalog_title 변환 결과 확인.
    """

@router.get("/matching-samples")
async def get_matching_samples(
    limit: int = 20,
    status: Optional[str] = None,  # matched, unmatched
) -> MatchingSamplesResponse:
    """NAS ↔ Sheets 매칭 샘플 조회."""

@router.get("/coverage")
async def get_validation_coverage() -> CoverageResponse:
    """전체 커버리지 통계.

    Returns:
        - title_generation_rate: 제목 생성률
        - matching_rate: 매칭률
        - by_project: 프로젝트별 통계
    """
```

---

## 7. 구현 순서

### Step 1: Phase 1 - 제목 생성 (Day 1)

```bash
# 1. title_generator.py 생성
# 2. catalog_builder_service.py 수정
# 3. 기존 데이터 마이그레이션 (regenerate-titles API)
# 4. 테스트
```

### Step 2: Phase 2 - Sheets 동기화 (Day 2)

```bash
# 1. HandClip 모델에 nas_folder_link 컬럼 추가
# 2. Alembic 마이그레이션
# 3. sheets_sync_service.py 구현
# 4. 동기화 API 추가
# 5. 테스트
```

### Step 3: Phase 3 - 경로 매칭 (Day 2-3)

```bash
# 1. path_matcher.py 구현
# 2. 매칭 API 추가
# 3. 기존 HandClip에 video_file_id 설정
# 4. 테스트
```

### Step 4: Phase 4 - Validation (Day 3)

```bash
# 1. validation.py API 구현
# 2. 프론트엔드 검증 페이지 추가
# 3. E2E 테스트
```

---

## 8. 성공 기준

| 지표 | 목표 | 현재 | Phase |
|------|------|------|-------|
| Title Generation Rate | ≥ 95% | 0% | Phase 1 |
| Sheets Sync Count | 2,500+ | 0 | Phase 2 |
| NAS ↔ Sheets Match Rate | ≥ 90% | 0% | Phase 3 |
| Validation API Coverage | 4 endpoints | 0 | Phase 4 |

---

## 9. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Sheets API 인증 실패 | Phase 2 차단 | 서비스 계정 키 확인 |
| 경로 형식 불일치 | 매칭률 저하 | 정규화 규칙 보완 |
| 대용량 데이터 처리 | 성능 저하 | 배치 처리, 인덱스 추가 |

---

**승인 후 Phase 1부터 구현을 시작합니다.**
