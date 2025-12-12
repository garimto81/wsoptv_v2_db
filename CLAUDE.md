# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PokerVOD** - 포커 비디오 카탈로그 시스템. NAS 스토리지(19TB+, 1,948 파일)의 영상과 Google Sheets 핸드 분석 데이터를 통합 관리.

### 핵심 목적 (Core Purpose)

1. **데이터 통합**: NAS 파일 + Google Sheets → PostgreSQL DB 통합
2. **Netflix 스타일 카탈로그**: 계층 구조 → 플랫 카탈로그 변환 (`/api/v1/contents/*`)
3. **제목 자동 생성**: 파일명 → 사용자 친화적 제목 (예: `10-wsop-2024-be-ev-21-...` → "WSOP 2024 Event #21 Final Table")

| 계층 | 기술 |
|------|------|
| Backend | FastAPI + Python 3.11+ |
| Database | PostgreSQL 16 (Docker) |
| ORM | SQLAlchemy 2.0 (Mapped 패턴) |
| Migration | Alembic |
| Frontend | Next.js 16 + React 19 + TailwindCSS 4 |
| Container | Docker Compose |

## Build & Run Commands

```bash
# Docker 실행 (권장)
docker-compose up -d                    # 전체 시스템 (postgres:5435, backend:8004, frontend:3001)

# Backend 로컬 개발
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Migration (backend/ 디렉토리에서)
alembic upgrade head                    # 마이그레이션 적용
alembic revision --autogenerate -m "description"  # 새 마이그레이션 생성

# Tests (단일 테스트 권장 - 전체 테스트는 시간 소요)
pytest tests/unit/services/test_file_parser.py -v
pytest tests/unit/api/test_health.py -v
pytest tests/unit/services/test_title_generator.py -v

# Frontend
cd frontend
npm install && npm run dev              # http://localhost:3000
npm run lint                            # ESLint
```

## Architecture

### Data Flow

```
NAS (SMB) → NASFile → ParserFactory → CatalogBuilderService → Catalog Entities
                                                                    ↓
                                          Episode ← Event ← Season ← Project
                                              ↓
                                          VideoFile ← NASFile (링크)
                                              ↓
                                          HandClip ←→ Tag, Player (N:N)
                                              ↑
                                      GoogleSheetSync
```

### Service 계층 구조

```
API (api/v1/)
    ├── contents.py        # Netflix-style browse/featured/top10
    ├── projects.py        # 프로젝트 CRUD
    ├── nas.py             # NAS 파일/폴더/동기화
    └── quality.py         # 데이터 품질 대시보드
         ↓
Services (services/)
    ├── catalog/           # project_service, season_service, event_service, episode_service
    │   └── catalog_builder_service.py  # NAS → Catalog 자동 생성 (핵심)
    ├── file_parser/       # ParserFactory + 8개 파서 (WSOP, GGM, GOG, PAD, MPP, Generic)
    │   └── title_generator.py  # 파일명 → display_title, catalog_title 변환
    ├── nas_inventory/     # smb_scanner, folder_service, file_service, sync_service
    ├── sheets_sync/       # Google Sheets 연동 (row_mapper, sync_engine)
    ├── hand_analysis/     # hand_clip_service, tag_service, player_service
    └── matching/          # path_matcher (NAS ↔ VideoFile 매칭)
         ↓
Models (models/)           # 11개 ORM 모델 (SQLAlchemy 2.0 Mapped 패턴)
```

### 11 ORM Models

| Block | Models |
|-------|--------|
| A - NAS | NASFolder, NASFile |
| B - Catalog | Project, Season, Event, Episode, VideoFile |
| C - Analysis | HandClip, Tag, Player (hand_clip_tags, hand_clip_players N:N) |
| D - Sync | GoogleSheetSync |

## Design Principles

| 원칙 | 설명 |
|------|------|
| ORM Only | Raw SQL (`text()`) 사용 금지, SQLAlchemy ORM만 사용 |
| Mapped Pattern | `Mapped[T]`, `mapped_column()` 필수 |
| Service Layer | API → Service → Model (직접 Model 접근 금지) |
| Async First | 모든 DB 작업은 `AsyncSession` 사용 |

## File Parsers (8개)

`ParserFactory.parse(file_name, file_path)` → `ParsedMetadata`

| Parser | 패턴 예시 |
|--------|----------|
| WSOPBracelet | `10-wsop-2024-be-ev-21-...` |
| WSOPCircuit | `WCLA24-001.mp4` |
| WSOPArchive | `wsop-2024-me-nobug.mp4` |
| GGMillions | `240615_Super High Roller...with Phil Ivey.mp4` |
| GOG | `E001_GOG_final_edit_...` |
| PAD | `pad-s1-ep01-abc.mp4` |
| MPP | `$1M GTD $10K Main Event Day 2.mp4` |
| Generic | 매칭 실패 시 fallback |

## API Endpoints

| Endpoint | 용도 |
|----------|------|
| `GET /api/v1/contents/browse` | **핵심** Netflix-style 메인 페이지 |
| `GET /api/v1/contents/featured` | Hero 배너 콘텐츠 |
| `GET /api/v1/contents/top10` | Top 10 리스트 |
| `GET /api/v1/projects` | 프로젝트 CRUD |
| `POST /api/v1/nas/sync` | NAS 동기화 실행 |
| `GET /api/v1/quality/*` | 데이터 품질 대시보드 |
| `GET /api/v1/health` | 헬스체크 |

## Docker Ports

| Service | Port | 용도 |
|---------|------|------|
| PostgreSQL | 5435 | DB 직접 접근 |
| Backend | 8004 | API (Swagger: /docs) |
| Frontend | 3001 | Next.js 앱 |

## Data Sources

- **NAS**: `\\10.10.100.122\docker\GGPNAs\ARCHIVE` (SMB)
- **Google Sheets**: metadata_archive, iconik_metadata
