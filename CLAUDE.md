# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PokerVOD** - 포커 비디오 카탈로그 시스템. NAS 스토리지(19TB+, 1,948 파일)의 영상과 Google Sheets 핸드 분석 데이터를 통합 관리.

### 핵심 목적 (Core Purpose)

1. **데이터 통합 분석**: NAS 파일 + Google Sheets → DB 통합
2. **Netflix 스타일 단일 계층 카탈로그 생성**: 계층 구조 → 플랫 카탈로그 변환
3. **제목 자동 생성**: 파일명 → 사용자 친화적 제목 (예: `10-wsop-2024-be-ev-21-...` → "WSOP 2024 Event #21 Final Table")
4. **프론트엔드 전달**: `/api/v1/contents/*` API로 플랫 카탈로그 제공

| 계층 | 기술 |
|------|------|
| Backend | FastAPI + Python 3.11+ |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 (Mapped 패턴) |
| Migration | Alembic |
| Frontend | React + TypeScript |
| Container | Docker Compose |

## Build & Run Commands

```bash
# 전체 시스템 실행
docker-compose up -d

# Backend 개발
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Migration
alembic upgrade head              # 마이그레이션 적용
alembic revision --autogenerate -m "description"  # 새 마이그레이션 생성
alembic downgrade -1              # 롤백

# Tests
pytest tests/test_specific.py -v  # 단일 테스트
pytest tests/ -v                  # 전체 테스트 (주의: 장시간 소요)

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture

```
Project → Season → Event → Episode → VideoFile
                                  → HandClip (N:N Tag, Player)

NASFolder → NASFile ↔ VideoFile
GoogleSheetSync → HandClip
```

**11개 ORM 모델**: Project, Season, Event, Episode, VideoFile, HandClip, Tag, Player, GoogleSheetSync, NASFolder, NASFile

## Project Structure

```
backend/
├── alembic/           # Migration 스크립트
├── src/
│   ├── models/        # SQLAlchemy ORM 모델 (11개)
│   ├── services/      # 비즈니스 로직
│   │   └── file_parser/  # 프로젝트별 파일명 파서
│   ├── api/           # REST 엔드포인트
│   ├── schemas/       # Pydantic DTO
│   └── main.py
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── store/
```

## Design Principles

| 원칙 | 설명 |
|------|------|
| Schema as Code | ORM 모델이 유일한 스키마 정의 |
| ORM Only | Raw SQL (`text()`) 사용 금지 |
| Mapped Pattern | SQLAlchemy 2.0 `Mapped[T]` 필수 |
| Service Layer | API → Service → Model 계층 구조 |

## 7 File Parsers

| Parser | 패턴 |
|--------|------|
| WSOPBracelet | `{번호}-wsop-{연도}-be-ev-{이벤트}-...` |
| WSOPCircuit | `WCLA{YY}-{번호}.mp4` |
| WSOPArchive | `wsop-{연도}-me-nobug.mp4` |
| GGMillions | `{YYMMDD}_Super High Roller...with {플레이어}.mp4` |
| GOG | `E{번호}_GOG_final_edit_...` |
| PAD | `pad-s{시즌}-ep{번호}-{코드}.mp4` |
| MPP | `${GTD금액} GTD ${바이인} {이벤트} {Day}.mp4` |

## Data Sources

- **NAS**: `\\10.10.100.122\docker\GGPNAs\ARCHIVE`
- **Google Sheets**:
  - metadata_archive (핸드 분석): `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4`
  - iconik_metadata (핸드 DB): `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk`

## API Endpoints

| Base | 용도 |
|------|------|
| `/api/v1/contents/*` | **핵심** - Netflix-style 플랫 카탈로그 (browse, featured, top10) |
| `/api/v1/projects` | 프로젝트 CRUD |
| `/api/v1/nas/*` | NAS 파일/폴더/동기화 |
| `/api/v1/quality/*` | 데이터 품질 대시보드 |
| `/health` | 헬스체크 |

## Docker Access

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8080 |
| API Docs | http://localhost:8080/api/docs |
| API Direct | http://localhost:9000 |
