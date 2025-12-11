# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-11

### Added
- PRD 핵심 목적 섹션 (1.2) - 데이터 통합 분석, Netflix 스타일 카탈로그, 제목 자동 생성
- Contents API 문서화 (섹션 10.3) - `/api/v1/contents/*` 엔드포인트
- 카탈로그 아이템 스키마 (섹션 10.2.1) - 프론트엔드 전달 구조
- NAS 분석 스크립트 (`analyze_nas.py`) - 숨김 파일 분류

### Changed
- PRD 상태 Draft → Active
- CLAUDE.md 핵심 목적 섹션 추가
- API 엔드포인트 강조 (`/api/v1/contents/*` 핵심 표시)

### Fixed
- 문서 정합성 검증 완료 (PRD ↔ 코드 ↔ CLAUDE.md)

## [1.0.0] - 2025-12-10

### Added
- Phase 1-6: 백엔드 API 구현 완료
- Phase 7: 프론트엔드 대시보드 (Next.js 16 + React 19)
- Phase 8: Docker Compose 배포
- 11개 ORM 모델 (Project, Season, Event, Episode, VideoFile, HandClip, Tag, Player, NASFolder, NASFile, GoogleSheetSync)
- 7개 파일 파서 (WSOP Bracelet, WSOP Circuit, WSOP Archive, GG Millions, GOG, PAD, MPP)
- Netflix 스타일 Contents API (`/api/v1/contents/*`)
- NAS 동기화 서비스 (19TB+, 1,948 파일)
- Google Sheets 연동
- 데이터 품질 대시보드

### Technical Stack
- Backend: FastAPI + Python 3.11+
- Database: PostgreSQL 15+
- ORM: SQLAlchemy 2.0 (Mapped Pattern)
- Frontend: Next.js 16 + React 19 + TailwindCSS 4
- Container: Docker Compose
