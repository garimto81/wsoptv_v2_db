# PRD: PokerVOD - 포커 비디오 카탈로그 시스템

> **버전**: 1.1.0 | **작성일**: 2025-12-11 | **상태**: Active

---

## 1. Executive Summary

### 1.1 프로젝트 개요

**PokerVOD**는 GGP Production의 포커 영상 콘텐츠를 체계적으로 관리하는 비디오 카탈로그 시스템입니다. NAS 스토리지의 영상 파일과 Google Sheets의 핸드 분석 데이터를 통합하여 Netflix 스타일의 미디어 라이브러리를 구축합니다.

### 1.2 핵심 목적 (Core Purpose)

이 시스템의 **핵심 목적**은 다음 3가지입니다:

#### 1.2.1 데이터 통합 분석

```
┌─────────────────┐     ┌─────────────────┐
│   NAS Storage   │     │  Google Sheets  │
│  (1,948 파일)   │     │   (2,500+ 행)   │
│  - 영상 파일     │     │  - 핸드 분석     │
│  - 파일 경로     │     │  - 타임코드      │
│  - 메타데이터    │     │  - 태그/플레이어  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌─────────────────────┐
         │   통합 분석 엔진     │
         │  - 파일명 파싱       │
         │  - 경로 매칭         │
         │  - 메타데이터 추출   │
         └──────────┬──────────┘
                    ▼
         ┌─────────────────────┐
         │   단일 계층 카탈로그  │
         └─────────────────────┘
```

#### 1.2.2 Netflix 스타일 단일 계층 카탈로그 생성

**기존 구조 (계층적)**:
```
Project (WSOP)
  └── Season (2024)
        └── Event (#21 $25K NLH)
              └── Episode (Final Table)
                    └── VideoFile (10-wsop-2024-be-ev-21-...)
```

**목표 구조 (플랫 카탈로그)**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    CATALOG ITEMS (플랫)                          │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│ │ 카드 1  │ │ 카드 2  │ │ 카드 3  │ │ 카드 4  │ │ 카드 5  │   │
│ │ ─────── │ │ ─────── │ │ ─────── │ │ ─────── │ │ ─────── │   │
│ │ WSOP    │ │ WSOP    │ │ GGM     │ │ PAD     │ │ GOG     │   │
│ │ 2024    │ │ 2024    │ │ 2025    │ │ S13     │ │ E05     │   │
│ │ Event21 │ │ Event22 │ │ FT      │ │ EP10    │ │ Final   │   │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**핵심 개념**:
- 프론트엔드는 **계층 구조를 몰라도** 카탈로그 아이템만으로 브라우징 가능
- 각 카탈로그 아이템은 **독립적인 단위**로 렌더링
- 필터/정렬은 **플랫 리스트** 기반 (Netflix, YouTube 스타일)

#### 1.2.3 적절한 제목 자동 생성

**파일명 → 사용자 친화적 제목 변환**:

| 원본 파일명 | 생성된 제목 |
|------------|------------|
| `10-wsop-2024-be-ev-21-25k-nlh-hr-ft.mp4` | WSOP 2024 Event #21 $25K NLH High Roller - Final Table |
| `WCLA24-15.mp4` | 2024 WSOP Circuit LA - Clip #15 |
| `250507_Super High Roller...with Joey Ingram.mp4` | GGMillions Super High Roller Final Table ft. Joey Ingram |
| `E05_GOG_final_edit_클린본.mp4` | Game of Gold Episode 5 (Clean) |
| `pad-s13-ep10-1234.mp4` | Poker After Dark S13 E10 |

**제목 필드 구분**:

| 필드 | 용도 | 예시 |
|------|------|------|
| `file_name` | 원본 파일명 | `10-wsop-2024-be-ev-21-25k-nlh-hr-ft.mp4` |
| `display_title` | UI 표시용 전체 제목 | WSOP 2024 Event #21 $25K NLH HR Final Table |
| `catalog_title` | 카탈로그 카드 제목 (짧은 버전) | WSOP 2024 #21 Final Table |

### 1.3 비즈니스 목표

| 목표 | 설명 |
|------|------|
| **콘텐츠 통합 관리** | 6개 포커 시리즈 (WSOP, HCL, GGMillions 등) 중앙 집중 관리 |
| **메타데이터 자동화** | 파일명 파싱 → 자동 분류 → 검색 최적화 |
| **핸드 분석 연동** | Google Sheets 핸드 데이터 ↔ 영상 타임코드 매핑 |
| **OTT 서비스 준비** | 카탈로그 기반 스트리밍 서비스 확장 가능 |

### 1.3 기술 스택

| 계층 | 기술 | 버전 |
|------|------|------|
| **Backend** | FastAPI + Python | 3.11+ |
| **Database** | PostgreSQL | 15+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Migration** | Alembic | 1.13+ |
| **Frontend** | React + TypeScript | 19+ |
| **Container** | Docker Compose | 3.8+ |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           POKERVOD SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │  NAS Storage │     │Google Sheets │     │  PostgreSQL  │            │
│  │  (19TB+)     │     │  (2 Sheets)  │     │   Database   │            │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘            │
│         │                    │                    │                     │
│         ▼                    ▼                    ▼                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Backend                             │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │   │
│  │  │  NAS Sync │  │  Sheets   │  │  Catalog  │  │   REST    │    │   │
│  │  │  Service  │  │  Service  │  │  Service  │  │    API    │    │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    React Dashboard                               │   │
│  │          Catalog Browser │ Sync Monitor │ Admin Panel            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Design Principles

| 원칙 | 설명 |
|------|------|
| **Schema as Code** | ORM 모델이 유일한 스키마 정의 (Single Source of Truth) |
| **Type Safety** | SQLAlchemy 2.0 Mapped 패턴으로 완전한 타입 안전성 |
| **Migration First** | 모든 스키마 변경은 Alembic 마이그레이션으로 관리 |
| **ORM Only** | Raw SQL 사용 금지, 모든 쿼리는 ORM으로 작성 |
| **Service Layer** | 비즈니스 로직은 Service 계층에 집중 |

---

## 3. Data Sources

### 3.1 NAS Storage Overview

**NAS 경로**: `\\10.10.100.122\docker\GGPNAs\ARCHIVE`

```
ARCHIVE/                              # 총 19.52TB, 1,912 파일
├── GGMillions/                       # Super High Roller (13개)
├── GOG 최종/                         # GOG 시리즈 (24개, 12 에피소드 x 2 버전)
├── HCL/                              # Hustler Casino Live (준비중)
├── MPP/                              # Mediterranean Poker Party (11개)
├── PAD/                              # Poker After Dark (45개)
└── WSOP/                             # World Series of Poker (1,279개)
    ├── WSOP ARCHIVE (PRE-2016)/      # 1973~2016 역사 아카이브
    ├── WSOP Bracelet Event/          # 브레이슬릿 이벤트
    │   ├── WSOP-EUROPE/
    │   ├── WSOP-LAS VEGAS/
    │   └── WSOP-PARADISE/
    └── WSOP Circuit Event/           # 서킷 이벤트
```

### 3.2 Project Statistics

| 프로젝트 | 파일 수 | 용량 | 상태 |
|----------|---------|------|------|
| **WSOP** | 1,279 | ~18TB | 활성 |
| **PAD** | 45 | ~200GB | 완료 |
| **GOG 최종** | 24 | ~50GB | 완료 |
| **GGMillions** | 13 | ~100GB | 활성 |
| **MPP** | 11 | ~100GB | 활성 |
| **HCL** | 1 | 준비중 | 준비중 |
| **비디오 합계** | **1,373** | **~19.52TB** | - |
| 메타데이터 (._*) | 518 | 2.1MB | 숨김 처리 |
| 시스템 (Thumbs.db) | 14 | 258KB | 숨김 처리 |

---

### 3.3 Project-specific Folder Structures

#### 3.3.1 GGMillions (13 files)

```
GGMillions/
├── 250507_Super High Roller Poker FINAL TABLE with Joey ingram.mp4
├── 250514_Super High Roller Poker FINAL TABLE with Fedor Holz.mp4
├── 250521_Super High Roller Poker FINAL TABLE with Xuan Liu.mp4
└── ... (총 13개)
```

**파일명 패턴**:
- 패턴 A: `{YYMMDD}_Super High Roller Poker FINAL TABLE with {플레이어}.mp4`
- 패턴 B: `Super High Roller Poker FINAL TABLE with {플레이어}.mp4`

#### 3.3.2 GOG 최종 (24 files)

```
GOG 최종/
├── e01/
│   ├── E01_GOG_final_edit_231106.mp4
│   └── E01_GOG_final_edit_클린본.mp4
├── e02/ ~ e12/
│   └── ... (동일 구조)
```

**파일명 패턴**:
- Final Edit: `E{번호}_GOG_final_edit_{YYYYMMDD}[_수정].mp4`
- Clean: `E{번호}_GOG_final_edit_클린본_{YYYYMMDD}.mp4`

#### 3.3.3 PAD (45 files)

```
PAD/
├── PAD S12/          # 시즌 12 (21 에피소드)
│   └── pad-s12-ep{01-21}-{코드}.mp4
└── PAD S13/          # 시즌 13 (23 에피소드)
    └── PAD_S13_EP{01-23}_{버전}-{코드}.mp4
```

**파일명 패턴**:
- S12: `pad-s12-ep{번호}-{코드}.mp4`
- S13: `PAD_S13_EP{번호}_{버전}-{코드}.mp4`

#### 3.3.4 MPP (11 files)

```
MPP/
└── 2025 MPP Cyprus/
    ├── $1M GTD   $1K PokerOK Mystery Bounty/
    │   └── $1M GTD   $1K PokerOK Mystery Bounty ? Day {1A,1C,Final}.mp4
    ├── $2M GTD   $2K Luxon Pay Grand Final/
    └── $5M GTD   $5K MPP Main Event/
```

**파일명 패턴**: `${GTD금액} GTD   ${바이인} {이벤트명} ? {Day/Final}.mp4`

#### 3.3.5 WSOP (1,279 files)

**WSOP ARCHIVE (PRE-2016)**:
```
WSOP ARCHIVE (PRE-2016)/
├── WSOP 1973/     # wsop-1973-me-nobug.mp4
├── WSOP 2003/     # 7개 + Best Of (Moneymaker 시즌)
├── WSOP 2004/     # 22개 에피소드
├── WSOP 2005/     # 32개 에피소드
└── ... ~ WSOP 2016/
```

**WSOP Bracelet LAS VEGAS (2024)**:
```
2024 WSOP-LAS VEGAS (PokerGo Clip)/
├── Clean/         # 원본 클린 버전 (38개)
│   └── {번호}-wsop-2024-be-ev-{이벤트}-{내용}-clean.mp4
└── Mastered/      # 마스터링 버전
    └── {번호}-wsop-2024-be-ev-{이벤트}-{내용}.mp4
```

**파일명 패턴 (2024 Bracelet)**:
```
{번호}-wsop-{연도}-be-ev-{이벤트번호}-{바이인}-{게임}-{추가정보}.mp4

예시: 10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten-reclaims-chip-lead.mp4
├─ 클립번호: 10
├─ 연도: 2024
├─ 타입: BE (Bracelet Event)
├─ 이벤트: 21
├─ 바이인: 25K
├─ 게임: NLH
├─ HR: High Roller
├─ FT: Final Table
└─ 내용: schutten-reclaims-chip-lead
```

**WSOP Circuit (2024 LA)**:
```
2024 WSOP Circuit LA/
├── 2024 WSOP-C LA STREAM/     # 풀 스트림 (11개)
│   └── 2024 WSOP Circuit Los Angeles - {이벤트} [{Day}].mp4
└── 2024 WSOP-C LA SUBCLIP/    # 하이라이트 (29개)
    └── WCLA24-{01-29}.mp4
```

---

### 3.4 File Format Summary

| 포맷 | 확장자 | 용도 | 주요 위치 |
|------|--------|------|----------|
| H.264/AVC | .mp4 | 최종 배포용 | 전체 |
| ProRes | .mov | 방송/편집용 | ARCHIVE (PRE-2016) |
| MXF | .mxf | 방송/아카이브 | ARCHIVE (PRE-2016) |
| AVI | .avi | 레거시 | 1973 |

### 3.5 Version Types

| 버전 타입 | 설명 | 파일명 특징 |
|----------|------|------------|
| Clean | 원본 클린 버전 | `-clean`, `클린본` |
| Mastered | 마스터링 완료 | Mastered 폴더 |
| Stream | 풀 스트림 녹화 | STREAM 폴더 |
| Subclip | 하이라이트 클립 | SUBCLIP 폴더 |
| Final Edit | 최종 편집본 | `final_edit` |
| No Bug | 버그 없는 버전 | `-nobug` |
| PGM | 프로그램 출력 | `pgm` |
| HiRes | 고해상도 버전 | `HiRes` |

---

## 4. Google Sheets Integration

### 4.1 Sheet 1: metadata_archive (핸드 분석 시트)

**시트 ID**: `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4`
**행 수**: 40+

| # | 컬럼명 | 데이터 타입 | 샘플 값 | DB 매핑 |
|---|--------|------------|---------|---------|
| 1 | File No. | INTEGER | 1, 2, 3... | `hand_clips.clip_number` |
| 2 | File Name | VARCHAR(500) | "2024 WSOP Circuit LA..." | `episodes.title` 매칭용 |
| 3 | **Nas Folder Link** | TEXT | `\\10.10.100.122\...` | `video_files.file_path` (**핵심 연동**) |
| 4 | In | TIME | "6:58:55" | `hand_clips.timecode` |
| 5 | Out | TIME | "7:00:47" | `hand_clips.timecode_end` |
| 6 | Hand Grade | VARCHAR(10) | "★", "★★", "★★★" | `hand_clips.hand_grade` |
| 7 | Winner | VARCHAR(50) | "JJ", "QQ", "AA" | `hand_clips.winner_hand` |
| 8 | Hands | VARCHAR(100) | "88 vs JJ" | `hand_clips.hands_involved` |
| 9-11 | Tag (Player) 1~3 | VARCHAR(100) | "Phil Hellmuth" | `hand_clip_players` (N:N) |
| 12-19 | Tag (Poker Play) 1~7 | VARCHAR(50) | "Cooler", "Bluff" | `hand_clip_tags` (N:N) |
| 20-21 | Tag (Emotion) 1~2 | VARCHAR(50) | "Excitement" | `hand_clip_tags` (N:N) |

**특성**:
- 다중 태그 시스템 (Player 3개, PokerPlay 7개, Emotion 2개)
- 타임코드 형식: `H:MM:SS` 또는 `HH:MM:SS`
- **핵심**: `Nas Folder Link` → `video_files.file_path` 매칭 → `hand_clips.video_file_id` 설정

### 4.2 Sheet 2: iconik_metadata (핸드 데이터베이스)

**시트 ID**: `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk`
**행 수**: 2,500+

| # | 컬럼명 | 데이터 타입 | 샘플 값 | DB 매핑 |
|---|--------|------------|---------|---------|
| 1 | id | UUID | `4fcb98f2-ee5b-11ef-...` | `hand_clips.id` |
| 2 | title | VARCHAR(500) | `7-wsop-2024-be-ev-12...` | `hand_clips.title` |
| 3 | time_start_ms | INTEGER | (밀리초) | `hand_clips.start_seconds` |
| 4 | time_end_ms | INTEGER | (밀리초) | `hand_clips.end_seconds` |
| 5 | Description | TEXT | "COOLER HAND..." | `hand_clips.description` |
| 6 | ProjectName | VARCHAR(50) | `WSOP` | `projects.code` |
| 7 | Year_ | INTEGER | `2024` | `seasons.year` |
| 8 | Location | VARCHAR(100) | `LAS VEGAS` | `seasons.location` |
| 9 | Venue | VARCHAR(200) | `$1,500 NLH 6-MAX` | `events.name` |
| 10 | Source | VARCHAR(20) | `PGM`, `Clean` | `video_files.version_type` |
| 11 | PlayersTags | TEXT | `Phil Hellmuth, ...` | 쉼표 구분 → `players` |
| 12 | HandGrade | VARCHAR(10) | `★★★` | `hand_clips.hand_grade` |
| 13 | HANDTag | VARCHAR(100) | `QQ vs KK` | `hand_clips.hands_involved` |
| 14 | PokerPlayTags | TEXT | `Cooler, Bluff` | 쉼표 구분 → `tags` |
| 15 | Emotion | VARCHAR(100) | `excitement, relief` | 쉼표 구분 → `tags` |
| 16 | GameType | VARCHAR(50) | `NLHE`, `PLO` | `events.game_type` |
| 17 | RUNOUTTag | VARCHAR(50) | `river, turn` | `tags` (runout) |
| 18 | EPICHAND | VARCHAR(100) | `Straight Flush` | `tags` (epic_hand) |
| 19 | Adjective | VARCHAR(100) | `brutal, incredible` | `tags` (adjective) |

**특성**:
- UUID 기반 ID 사용
- 다중 값 컬럼이 쉼표로 구분됨 → 정규화 필요
- 70-80% 데이터가 부분적으로 채워짐 → nullable 허용

### 4.3 Tag Categories (5개)

| 카테고리 | 출처 | 샘플 값 | DB 저장 |
|----------|------|--------|---------|
| `poker_play` | Sheet 1/2 | Preflop All-in, Cooler, Bluff, Hero Call, Suckout, Bad Beat | `tags` 테이블 |
| `emotion` | Sheet 1/2 | Stressed, Excitement, Relief, Pain, Laughing | `tags` 테이블 |
| `epic_hand` | Sheet 2 | Royal Flush, Straight Flush, Quads, Full House | `tags` 테이블 |
| `runout` | Sheet 2 | runner runner, 1out, dirty, river, turn | `tags` 테이블 |
| `adjective` | Sheet 2 | brutal, incredible, insane, sick | `tags` 테이블 |

### 4.4 Data Mapping Flow

```
Sheet 데이터              →     DB 구조
────────────────────────────────────────────
ProjectName              →     projects
Year_ + Location         →     seasons
Venue                    →     events
File Name                →     episodes
Nas Folder Link          →     video_files.file_path
id + title + In/Out      →     hand_clips
PlayersTags              →     players ↔ hand_clip_players (N:N)
PokerPlayTags + ...      →     tags ↔ hand_clip_tags (N:N)
```

---

## 5. Personas

### 5.1 콘텐츠 아키비스트 (Content Archivist)

**이름**: 김영상
**역할**: 포커 비디오 콘텐츠 관리자

| 목표 | Pain Points | 니즈 |
|------|-------------|------|
| NAS 영상 체계적 분류 | 프로젝트별 파일명 규칙 상이 | 자동 스캔 및 분류 |
| 누락 콘텐츠 파악 | STREAM/SUBCLIP 연결 어려움 | 버전 추적 시스템 |
| Clean/Mastered 관리 | 연도/이벤트별 현황 불명확 | 완결성 대시보드 |

### 5.2 포커 분석가 (Poker Analyst)

**이름**: 박분석
**역할**: 핸드 분석 및 콘텐츠 큐레이션

| 목표 | Pain Points | 니즈 |
|------|-------------|------|
| Sheets ↔ DB 연동 | 영상-시트 수동 매칭 | 자동 매핑 |
| 태그 기반 검색 | 태그 일관성 유지 어려움 | 태그 자동완성/표준화 |
| 플레이어/이벤트별 통계 | 타임코드-영상 연결 누락 | 타임코드 기반 점프 |

### 5.3 OTT 서비스 운영자 (Service Operator)

**이름**: 이서비스
**역할**: 포커 OTT 플랫폼 운영

| 목표 | Pain Points | 니즈 |
|------|-------------|------|
| 프로젝트별 콘텐츠 서비스 | Mastered 파일 식별 어려움 | 품질별 필터링 |
| 하이라이트 클립 제공 | 라이선스 관리 복잡 | 서비스 상태 추적 |
| 다국어 자막 관리 | 신규 콘텐츠 업데이트 지연 | 자동 업데이트 알림 |

### 5.4 포커 팬 (End User)

**이름**: 최시청
**역할**: 포커 콘텐츠 시청자

| 목표 | Pain Points | 니즈 |
|------|-------------|------|
| 플레이어별 핸드 시청 | 플레이어/핸드 검색 불가 | 태그 기반 검색 |
| Epic Hand 검색 | 하이라이트만 보고 싶음 | 핸드 등급 필터 |
| Bad Beat, Cooler 검색 | 콘텐츠 분산 | 크로스 프로젝트 통합 검색 |

---

## 6. Database Schema

### 6.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CORE ENTITIES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Project ──1:N──▶ Season ──1:N──▶ Event ──1:N──▶ Episode                │
│     │                                              │                     │
│     │                                              ├──1:N──▶ VideoFile  │
│     │                                              │              │      │
│     │                                              └──1:N──▶ HandClip   │
│     │                                                          │   │    │
│     │                                              ┌───────────┘   │    │
│     │                                              ▼               ▼    │
│     └──────────────────────────────────────▶ NASFile    Tag ◀── Player  │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                           SYNC ENTITIES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GoogleSheetSync ◀───── 동기화 상태 추적                                 │
│                                                                          │
│  NASFolder ──1:N──▶ NASFile ◀───── NAS 인벤토리                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Base Configuration

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData, func
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

class Base(DeclarativeBase):
    """Global declarative base with naming conventions."""
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

class TimestampMixin:
    """Reusable timestamp columns."""
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)
```

### 6.3 Core Models

#### Project

```python
class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # WSOP, HCL, etc.
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    nas_base_path: Mapped[Optional[str]] = mapped_column(String(500))
    filename_pattern: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    seasons: Mapped[List["Season"]] = relationship(back_populates="project", cascade="all, delete-orphan")
```

**Project Codes (7개)**:
| Code | Name | Description |
|------|------|-------------|
| WSOP | World Series of Poker | 브레이슬릿/서킷 이벤트, 아카이브(1973~) |
| HCL | Hustler Casino Live | 캐시게임, 하이라이트 클립 |
| GGMILLIONS | GGMillions Super High Roller | 파이널 테이블 영상 |
| MPP | Mediterranean Poker Party | 토너먼트 영상 |
| PAD | Poker After Dark | TV 시리즈 (S12, S13) |
| GOG | Game of Gold | 에피소드 시리즈 |
| OTHER | Other Projects | 기타 콘텐츠 |

#### Season

```python
class Season(Base, TimestampMixin):
    __tablename__ = "seasons"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("pokervod.projects.id"))
    year: Mapped[int]
    name: Mapped[str] = mapped_column(String(200))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    sub_category: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="seasons")
    events: Mapped[List["Event"]] = relationship(back_populates="season")
```

**Sub-Categories (WSOP)**:
| Code | Description |
|------|-------------|
| ARCHIVE | 1973-2016 역사 아카이브 |
| BRACELET_LV | Las Vegas 브레이슬릿 |
| BRACELET_EU | Europe 브레이슬릿 |
| BRACELET_PARA | Paradise 브레이슬릿 |
| CIRCUIT | 서킷 이벤트 |
| SUPER_CIRCUIT | 슈퍼 서킷 |

#### Event

```python
class Event(Base, TimestampMixin):
    __tablename__ = "events"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    season_id: Mapped[UUID] = mapped_column(ForeignKey("pokervod.seasons.id"))
    event_number: Mapped[Optional[int]]
    name: Mapped[str] = mapped_column(String(500))
    name_short: Mapped[Optional[str]] = mapped_column(String(100))
    event_type: Mapped[Optional[str]] = mapped_column(String(50))
    game_type: Mapped[Optional[str]] = mapped_column(String(50))
    buy_in: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    gtd_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    venue: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="upcoming")

    # Relationships
    season: Mapped["Season"] = relationship(back_populates="events")
    episodes: Mapped[List["Episode"]] = relationship(back_populates="event")
```

**Event Types**:
| Type | Description |
|------|-------------|
| bracelet | 브레이슬릿 이벤트 |
| circuit | 서킷 이벤트 |
| super_circuit | 슈퍼 서킷 |
| high_roller | 하이롤러 |
| super_high_roller | 슈퍼 하이롤러 |
| cash_game | 캐시게임 |
| tv_series | TV 시리즈 |
| mystery_bounty | 미스터리 바운티 |
| main_event | 메인 이벤트 |

**Game Types**:
| Type | Description |
|------|-------------|
| NLHE | No Limit Hold'em |
| PLO | Pot Limit Omaha |
| PLO8 | Pot Limit Omaha Hi-Lo |
| Mixed | 믹스드 게임 |
| Stud | 스터드 |
| Razz | 라즈 |
| HORSE | H.O.R.S.E. |
| 2-7TD | 2-7 Triple Draw |

#### Episode

```python
class Episode(Base, TimestampMixin):
    __tablename__ = "episodes"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("pokervod.events.id"))
    episode_number: Mapped[Optional[int]]
    day_number: Mapped[Optional[int]]
    part_number: Mapped[Optional[int]]
    title: Mapped[Optional[str]] = mapped_column(String(500))
    episode_type: Mapped[Optional[str]] = mapped_column(String(50))
    table_type: Mapped[Optional[str]] = mapped_column(String(50))
    duration_seconds: Mapped[Optional[int]]

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="episodes")
    video_files: Mapped[List["VideoFile"]] = relationship(back_populates="episode")
    hand_clips: Mapped[List["HandClip"]] = relationship(back_populates="episode")
```

**Episode Types**: `full`, `highlight`, `recap`, `interview`, `subclip`
**Table Types**: `preliminary`, `day1`, `day2`, `day3`, `final_table`, `heads_up`

#### VideoFile

```python
class VideoFile(Base, TimestampMixin):
    __tablename__ = "video_files"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("pokervod.episodes.id", ondelete="SET NULL"))

    # File info
    file_path: Mapped[str] = mapped_column(String(1000), unique=True)
    file_name: Mapped[str] = mapped_column(String(500))
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    file_format: Mapped[Optional[str]] = mapped_column(String(20))
    file_mtime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Video metadata
    resolution: Mapped[Optional[str]] = mapped_column(String(20))
    video_codec: Mapped[Optional[str]] = mapped_column(String(50))
    audio_codec: Mapped[Optional[str]] = mapped_column(String(50))
    bitrate_kbps: Mapped[Optional[int]]
    duration_seconds: Mapped[Optional[int]]
    version_type: Mapped[Optional[str]] = mapped_column(String(20))
    is_original: Mapped[bool] = mapped_column(default=False)

    # Catalog display
    display_title: Mapped[Optional[str]] = mapped_column(String(500))
    content_type: Mapped[Optional[str]] = mapped_column(String(20))
    catalog_title: Mapped[Optional[str]] = mapped_column(String(300))
    is_catalog_item: Mapped[bool] = mapped_column(default=False)

    # Filtering
    is_hidden: Mapped[bool] = mapped_column(default=False)
    hidden_reason: Mapped[Optional[str]] = mapped_column(String(50))
    scan_status: Mapped[str] = mapped_column(String(20), default="pending")

    # Relationships
    episode: Mapped[Optional["Episode"]] = relationship(back_populates="video_files")
    hand_clips: Mapped[List["HandClip"]] = relationship(back_populates="video_file")
    nas_file: Mapped[Optional["NASFile"]] = relationship(back_populates="video_file")
```

**Version Types**: `clean`, `mastered`, `stream`, `subclip`, `final_edit`, `nobug`, `pgm`, `generic`, `hires`

### 6.4 Hand Clip Models

#### HandClip

```python
class HandClip(Base, TimestampMixin):
    __tablename__ = "hand_clips"
    __table_args__ = (
        UniqueConstraint("sheet_source", "sheet_row_number"),
        {"schema": "pokervod"}
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("pokervod.episodes.id", ondelete="SET NULL"))
    video_file_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("pokervod.video_files.id", ondelete="SET NULL"))

    # Sheet tracking
    sheet_source: Mapped[Optional[str]] = mapped_column(String(50))
    sheet_row_number: Mapped[Optional[int]]

    # Content
    title: Mapped[Optional[str]] = mapped_column(String(500))
    timecode: Mapped[Optional[str]] = mapped_column(String(20))
    timecode_end: Mapped[Optional[str]] = mapped_column(String(20))
    duration_seconds: Mapped[Optional[int]]
    notes: Mapped[Optional[str]] = mapped_column(Text)
    hand_grade: Mapped[Optional[str]] = mapped_column(String(10))  # ★, ★★, ★★★
    pot_size: Mapped[Optional[int]]
    winner_hand: Mapped[Optional[str]] = mapped_column(String(50))
    hands_involved: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    episode: Mapped[Optional["Episode"]] = relationship(back_populates="hand_clips")
    video_file: Mapped[Optional["VideoFile"]] = relationship(back_populates="hand_clips")
    tags: Mapped[List["Tag"]] = relationship(secondary="pokervod.hand_clip_tags", back_populates="hand_clips")
    players: Mapped[List["Player"]] = relationship(secondary="pokervod.hand_clip_players", back_populates="hand_clips")
```

#### Tag

```python
class Tag(Base, TimestampMixin):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("category", "name"),
        {"schema": "pokervod"}
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(50))  # poker_play, emotion, epic_hand, runout, adjective
    name: Mapped[str] = mapped_column(String(100))
    name_display: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    hand_clips: Mapped[List["HandClip"]] = relationship(secondary="pokervod.hand_clip_tags", back_populates="tags")
```

#### Player

```python
class Player(Base, TimestampMixin):
    __tablename__ = "players"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    name_display: Mapped[Optional[str]] = mapped_column(String(200))
    nationality: Mapped[Optional[str]] = mapped_column(String(100))
    hendon_mob_id: Mapped[Optional[str]] = mapped_column(String(50))
    total_live_earnings: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    wsop_bracelets: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    hand_clips: Mapped[List["HandClip"]] = relationship(secondary="pokervod.hand_clip_players", back_populates="players")
```

### 6.5 Sync Models

#### GoogleSheetSync

```python
class GoogleSheetSync(Base, TimestampMixin):
    __tablename__ = "google_sheet_sync"
    __table_args__ = (
        UniqueConstraint("sheet_id", "entity_type"),
        {"schema": "pokervod"}
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    sheet_id: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(50))
    last_row_synced: Mapped[int] = mapped_column(default=0)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
```

#### NASFolder

```python
class NASFolder(Base, TimestampMixin):
    __tablename__ = "nas_folders"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    folder_path: Mapped[str] = mapped_column(String(1000), unique=True)
    folder_name: Mapped[str] = mapped_column(String(500))
    parent_path: Mapped[Optional[str]] = mapped_column(String(1000))
    depth: Mapped[int] = mapped_column(default=0)

    # Statistics
    file_count: Mapped[int] = mapped_column(default=0)
    folder_count: Mapped[int] = mapped_column(default=0)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    # Metadata
    is_empty: Mapped[bool] = mapped_column(default=True)
    is_hidden_folder: Mapped[bool] = mapped_column(default=False)

    # Relationships
    files: Mapped[List["NASFile"]] = relationship(back_populates="folder")
```

#### NASFile

```python
class NASFile(Base, TimestampMixin):
    __tablename__ = "nas_files"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    file_path: Mapped[str] = mapped_column(String(1000), unique=True)
    file_name: Mapped[str] = mapped_column(String(500))
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    file_extension: Mapped[Optional[str]] = mapped_column(String(20))
    file_mtime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Classification
    file_category: Mapped[str] = mapped_column(String(20), default="other")  # video, metadata, system, archive, other
    is_hidden_file: Mapped[bool] = mapped_column(default=False)

    # Foreign keys
    video_file_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("pokervod.video_files.id", ondelete="SET NULL"))
    folder_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("pokervod.nas_folders.id", ondelete="SET NULL"))

    # Relationships
    video_file: Mapped[Optional["VideoFile"]] = relationship(back_populates="nas_file")
    folder: Mapped[Optional["NASFolder"]] = relationship(back_populates="files")
```

### 6.6 Schema Summary

| Model | Table | Columns | Purpose |
|-------|-------|---------|---------|
| Project | projects | 9 | 포커 시리즈 |
| Season | seasons | 10 | 연도별 시즌 |
| Event | events | 15 | 토너먼트/이벤트 |
| Episode | episodes | 12 | 개별 영상 단위 |
| VideoFile | video_files | 22 | 비디오 파일 메타데이터 |
| HandClip | hand_clips | 16 | 핸드 분석 클립 |
| Tag | tags | 8 | 태그 마스터 |
| Player | players | 9 | 플레이어 정보 |
| GoogleSheetSync | google_sheet_sync | 7 | 동기화 상태 |
| NASFolder | nas_folders | 11 | 폴더 구조 |
| NASFile | nas_files | 11 | 파일 인벤토리 |

**Total: 11 Models**

---

## 7. File Parser System

### 7.1 Parser Architecture

```
ParserFactory
    │
    ├── WSOPBraceletParser     # {번호}-wsop-{연도}-be-ev-{이벤트}...
    ├── WSOPCircuitParser      # WCLA24-{번호}.mp4
    ├── WSOPArchiveParser      # wsop-{연도}-me-nobug.mp4
    ├── GGMillionsParser       # {YYMMDD}_Super High Roller...
    ├── GOGParser              # E{번호}_GOG_final_edit...
    ├── PADParser              # pad-s{시즌}-ep{번호}...
    ├── MPPParser              # ${GTD} GTD   ${바이인}...
    └── GenericParser          # Fallback
```

### 7.2 Parser Patterns

| Parser | Pattern | Extracted Fields |
|--------|---------|-----------------|
| WSOPBracelet | `^(\d+)-wsop-(\d{4})-be-ev-(\d+)-...` | clip_number, year, event, buy_in, game, table |
| WSOPCircuit | `^WCLA(\d{2})-(\d+)\.(mp4|mov)$` | year, clip_number |
| GGMillions | `^(\d{6})?_?Super High Roller...with (.+)\.mp4$` | date, featured_player |
| GOG | `^E(\d{1,3})_GOG_final_edit_(클린본_)?...` | episode_number, version_type, edit_date |
| PAD | `^pad-s(\d+)-ep(\d+)-(\d+)\.mp4$` | season, episode, code |
| MPP | `^\$(\d+[MK]) GTD.*\? (.+)\.mp4$` | gtd_amount, day_info |

---

## 8. Migration System

### 8.1 Alembic Configuration

```
backend/
├── alembic/
│   ├── versions/
│   │   └── 001_initial_schema.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
```

### 8.2 Migration Workflow

```
1. Modify Model ────────▶ src/models/*.py
2. Generate Migration ──▶ alembic revision --autogenerate -m "description"
3. Review Script ───────▶ alembic/versions/xxx_description.py
4. Test Migration ──────▶ alembic upgrade head → downgrade -1 → upgrade head
5. Commit ──────────────▶ Model changes + Migration script
6. Deploy ──────────────▶ CI/CD runs: alembic upgrade head
```

### 8.3 Docker Integration

```yaml
services:
  api:
    command: >
      sh -c "alembic upgrade head &&
             uvicorn src.main:app --host 0.0.0.0 --port 8000"
```

---

## 9. Project Structure

```
pokervod/
├── backend/
│   ├── alembic/                    # Migration system
│   ├── alembic.ini
│   ├── src/
│   │   ├── models/                 # ORM Models (11 models)
│   │   │   ├── base.py
│   │   │   ├── project.py
│   │   │   ├── season.py
│   │   │   ├── event.py
│   │   │   ├── episode.py
│   │   │   ├── video_file.py
│   │   │   ├── hand_clip.py
│   │   │   ├── tag.py
│   │   │   ├── player.py
│   │   │   ├── google_sheet_sync.py
│   │   │   ├── nas_folder.py
│   │   │   └── nas_file.py
│   │   ├── services/               # Business Logic
│   │   │   ├── project_service.py
│   │   │   ├── catalog_service.py
│   │   │   ├── sync_service.py
│   │   │   ├── hand_clip_service.py
│   │   │   ├── nas_inventory_service.py
│   │   │   └── file_parser/
│   │   │       ├── base_parser.py
│   │   │       ├── wsop_parser.py
│   │   │       ├── ggmillions_parser.py
│   │   │       └── parser_factory.py
│   │   ├── api/                    # REST API
│   │   ├── schemas/                # Pydantic DTOs
│   │   ├── database.py
│   │   └── main.py
│   ├── tests/
│   ├── docker/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── store/
│   └── package.json
└── docs/
```

---

## 10. API Endpoints

### 10.1 Core APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | 프로젝트 목록 |
| GET | `/api/projects/{id}` | 프로젝트 상세 |
| GET | `/api/seasons` | 시즌 목록 (필터링) |
| GET | `/api/events` | 이벤트 목록 |
| GET | `/api/episodes/{id}/videos` | 에피소드 비디오 목록 |

### 10.2 Catalog APIs (프론트엔드 핵심)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/catalog` | 카탈로그 아이템 (플랫 리스트) |
| GET | `/api/catalog/stats` | 카탈로그 통계 |
| GET | `/api/catalog/filters` | 필터 옵션 |

#### 10.2.1 카탈로그 아이템 스키마 (프론트엔드 전달용)

**GET `/api/catalog`** - 프론트엔드가 소비하는 **단일 계층 카탈로그**:

```typescript
// 프론트엔드 CatalogItem 타입
interface CatalogItem {
  // 식별자
  id: string;                    // UUID

  // 제목 (핵심!)
  catalog_title: string;         // 카드 표시용 짧은 제목
  display_title: string;         // 상세 페이지용 전체 제목
  file_name: string;             // 원본 파일명

  // 분류 정보 (플랫하게 전달)
  project_code: string;          // "WSOP", "HCL", "GGMILLIONS", ...
  project_name: string;          // "World Series of Poker"
  year: number;                  // 2024
  event_name?: string;           // "Event #21 $25K NLH"
  episode_type?: string;         // "final_table", "day1", "highlight"

  // 미디어 정보
  duration_seconds?: number;
  resolution?: string;           // "1080p", "4K"
  file_format: string;           // "mp4", "mov"
  file_size_bytes: number;

  // 썸네일/포스터
  thumbnail_url?: string;
  poster_url?: string;

  // 필터링용 태그
  tags: string[];                // ["Cooler", "Bad Beat", "Final Table"]
  players: string[];             // ["Phil Hellmuth", "Daniel Negreanu"]
  game_type?: string;            // "NLHE", "PLO"

  // 상태
  is_available: boolean;         // 스트리밍 가능 여부
  created_at: string;            // ISO datetime
}

// API 응답
interface CatalogResponse {
  items: CatalogItem[];
  total: number;
  page: number;
  page_size: number;
  filters_applied: Record<string, any>;
}
```

**핵심 포인트**:
- 프론트엔드는 **계층 구조(Project→Season→Event→Episode)를 알 필요 없음**
- 모든 정보가 **플랫하게 펼쳐진 단일 객체**로 전달
- `catalog_title`과 `display_title`이 **자동 생성된 사용자 친화적 제목**

#### 10.2.2 필터 API

**GET `/api/catalog/filters`**:

```typescript
interface CatalogFilters {
  projects: { code: string; name: string; count: number }[];
  years: number[];
  game_types: string[];
  episode_types: string[];
  tags: { category: string; values: string[] }[];
}
```

#### 10.2.3 사용 예시

```typescript
// 프론트엔드에서의 사용
const { data } = useCatalog({
  project: "WSOP",
  year: 2024,
  tags: ["Final Table"],
  page: 1,
  pageSize: 20,
});

// 렌더링 - 계층 구조 몰라도 됨!
data.items.map(item => (
  <CatalogCard
    title={item.catalog_title}
    thumbnail={item.thumbnail_url}
    duration={item.duration_seconds}
    tags={item.tags}
  />
));
```

### 10.3 Contents APIs (실제 구현됨)

**Netflix-style 콘텐츠 브라우징 API** (`/api/v1/contents/*`):

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/contents/browse` | 메인 브라우징 페이지 (Featured + Rows) |
| GET | `/api/v1/contents/featured` | Hero Billboard 콘텐츠 |
| GET | `/api/v1/contents/top10` | 인기 Top 10 콘텐츠 |
| GET | `/api/v1/contents/category/{category}` | 카테고리별 콘텐츠 |
| GET | `/api/v1/contents/{content_id}` | 단일 콘텐츠 상세 |

**응답 스키마 (구현됨)**:

```typescript
// ContentItem - 플랫 카탈로그 아이템
interface ContentItem {
  id: string;
  title: string;           // 자동 생성된 제목
  description: string | null;
  thumbnail_url: string | null;
  backdrop_url: string | null;
  category: string;        // project_code
  year: number | null;
  duration_seconds: number | null;
  quality: string | null;
  tags: string[];
  progress: number | null; // Continue Watching용
}

// BrowseResponse - 메인 브라우징 페이지
interface BrowseResponse {
  featured: FeaturedContent | null;
  rows: ContentRow[];      // Continue Watching, Top 10, 프로젝트별 Row
}
```

### 10.4 Sync APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sync/status` | 동기화 상태 |
| POST | `/api/sync/trigger/{source}` | 동기화 시작 |
| GET | `/api/sync/hand-clips` | 핸드 클립 목록 |
| GET | `/api/sync/tree` | NAS 폴더 트리 |
| GET | `/api/sync/sheets/preview` | Sheets 미리보기 |

### 10.5 Health APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | 헬스 체크 |
| GET | `/api/health/db` | DB 상태 |

---

## 11. Development Guidelines

### 11.1 Coding Standards

| 규칙 | 설명 |
|------|------|
| **No Raw SQL** | `text()` 사용 금지, ORM 쿼리만 허용 |
| **Type Hints** | 모든 함수/변수에 타입 힌트 필수 |
| **Mapped Pattern** | SQLAlchemy 2.0 `Mapped[T]` 패턴 사용 |
| **Service Layer** | API → Service → Model 계층 구조 |
| **Factory Tests** | factory_boy로 테스트 데이터 생성 |

### 11.2 Pre-commit Hooks

```yaml
repos:
  - repo: local
    hooks:
      - id: no-raw-sql
        name: Prevent raw SQL usage
        entry: python scripts/check_raw_sql.py
        files: \.py$
        exclude: alembic/
```

---

## 12. Deployment

### 12.1 Docker Compose

```yaml
name: pokervod

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pokervod
      POSTGRES_USER: pokervod
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: ./backend
    command: sh -c "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0"
    ports:
      - "127.0.0.1:9000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - /z/GGPNAs/ARCHIVE:/nas/ARCHIVE:ro

  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - api

volumes:
  postgres_data:
```

### 12.2 Access URLs

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8080 |
| API Docs | http://localhost:8080/api/docs |
| WebSocket | ws://localhost:8080/ws/sync |

---

## 13. Timeline

| Phase | 기간 | 산출물 |
|-------|------|--------|
| **Phase 1: Foundation** | Week 1 | ORM Models (11개) + Alembic Setup |
| **Phase 2: Backend** | Week 2 | Services + API Endpoints |
| **Phase 3: Parsers** | Week 3 | 7개 File Parsers + NAS Sync |
| **Phase 4: Sheets** | Week 4 | Google Sheets 동기화 |
| **Phase 5: Frontend** | Week 5 | Dashboard + Catalog UI |

---

## 14. Success Metrics

| 지표 | 목표 |
|------|------|
| ORM Model Coverage | 100% (11/11 models) |
| Raw SQL Usage | 0 locations |
| Test Coverage | ≥ 90% |
| API Response Time | < 200ms (p95) |
| NAS Sync Accuracy | 100% (Windows 탐색기 일치) |
| Sheets Sync Accuracy | 100% (video_file_id 연결) |

---

## 15. Data Matching & Validation (v1.2.0 추가)

### 15.1 핵심 요구사항

시스템의 핵심 가치는 **단순 수치 통계가 아닌 실제 데이터 매칭 검증**입니다.

**검증 가능해야 하는 항목**:

| # | 검증 항목 | 소스 A | 소스 B | 매칭 키 |
|---|----------|--------|--------|---------|
| 1 | **제목 변환** | NASFile.file_name | VideoFile.display_title | 파싱 규칙 |
| 2 | **카탈로그 제목** | NASFile.file_name | VideoFile.catalog_title | 축약 규칙 |
| 3 | **NAS ↔ Sheets** | NASFile.file_path | HandClip.nas_folder_link | 경로 매칭 |
| 4 | **VideoFile ↔ HandClip** | VideoFile.id | HandClip.video_file_id | FK 연결 |

### 15.2 제목 자동 생성 규칙

#### 15.2.1 display_title (전체 제목)

**파일명 → 사용자 친화적 전체 제목 변환**:

| 프로젝트 | 원본 파일명 | 생성될 display_title |
|----------|------------|---------------------|
| WSOP Bracelet | `10-wsop-2024-be-ev-21-25k-nlh-hr-ft.mp4` | `WSOP 2024 Event #21 $25K NLH High Roller Final Table` |
| WSOP Circuit | `WCLA24-15.mp4` | `2024 WSOP Circuit LA - Clip #15` |
| GGMillions | `250507_Super High Roller...with Joey Ingram.mp4` | `GG Millions Super High Roller Final Table ft. Joey Ingram (2025-05-07)` |
| GOG | `E05_GOG_final_edit_클린본.mp4` | `Game of Gold Episode 5 (Clean Version)` |
| PAD | `pad-s13-ep10-1234.mp4` | `Poker After Dark S13 Episode 10` |
| MPP | `$1M GTD $1K PokerOK Mystery Bounty – Final.mp4` | `MPP 2025 $1M GTD $1K Mystery Bounty - Final Table` |

#### 15.2.2 catalog_title (카드용 짧은 제목)

| display_title | catalog_title |
|--------------|---------------|
| `WSOP 2024 Event #21 $25K NLH High Roller Final Table` | `WSOP 2024 #21 Final Table` |
| `2024 WSOP Circuit LA - Clip #15` | `WSOP-C LA Clip #15` |
| `Game of Gold Episode 5 (Clean Version)` | `GOG E05` |
| `Poker After Dark S13 Episode 10` | `PAD S13 E10` |

#### 15.2.3 변환 규칙

```python
# display_title 생성 규칙
def generate_display_title(metadata: ParsedMetadata) -> str:
    """파서 메타데이터에서 display_title 생성."""
    parts = []

    # 프로젝트명
    project_names = {
        "WSOP": "WSOP",
        "WSOP_CIRCUIT": "WSOP Circuit",
        "GGMILLIONS": "GG Millions",
        "GOG": "Game of Gold",
        "PAD": "Poker After Dark",
        "MPP": "MPP",
    }
    parts.append(project_names.get(metadata.project_code, metadata.project_code))

    # 연도
    if metadata.year:
        parts.append(str(metadata.year))

    # 이벤트 정보
    if metadata.event_number:
        parts.append(f"Event #{metadata.event_number}")

    # 바이인/게임타입
    if metadata.buy_in:
        parts.append(f"${metadata.buy_in}")
    if metadata.game_type:
        parts.append(metadata.game_type)

    # 테이블 타입
    table_names = {
        "ft": "Final Table",
        "final_table": "Final Table",
        "d1": "Day 1",
        "d2": "Day 2",
        "hu": "Heads Up",
    }
    if metadata.table_type:
        parts.append(table_names.get(metadata.table_type, metadata.table_type))

    return " ".join(parts)
```

### 15.3 NAS ↔ Google Sheets 매칭 규칙

#### 15.3.1 매칭 키: Nas Folder Link

Google Sheets의 `Nas Folder Link` 컬럼과 NASFile.file_path 매칭:

```
Sheets: \\10.10.100.122\docker\GGPNAs\ARCHIVE\WSOP\2024\event21.mp4
         ↓ 정규화
DB:     GGPNAs/ARCHIVE/WSOP/2024/event21.mp4
```

**정규화 규칙**:
1. UNC 경로 프리픽스 제거: `\\10.10.100.122\docker\` → ``
2. 백슬래시 → 슬래시: `\` → `/`
3. 대소문자 무시 매칭

#### 15.3.2 매칭 흐름

```
Google Sheets (metadata_archive)
    ↓ [동기화]
HandClip 테이블
    ↓ [nas_folder_link 파싱]
NASFile.file_path 매칭
    ↓ [video_file_id 설정]
VideoFile ↔ HandClip 연결 완료
```

### 15.4 검증 API (신규)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/validation/title-samples` | 제목 변환 샘플 (원본 → display_title → catalog_title) |
| GET | `/api/v1/validation/matching-samples` | NAS ↔ Sheets 매칭 샘플 |
| GET | `/api/v1/validation/mismatches` | 매칭 실패 목록 (원인 포함) |
| GET | `/api/v1/validation/coverage` | 전체 커버리지 통계 |

#### 15.4.1 title-samples 응답 스키마

```typescript
interface TitleSample {
  file_name: string;          // 원본 파일명
  display_title: string;      // 생성된 전체 제목
  catalog_title: string;      // 생성된 카드 제목
  parser_used: string;        // 사용된 파서
  parsed_metadata: {          // 파싱된 메타데이터
    project_code: string;
    year: number;
    event_number: number;
    // ...
  };
}

interface TitleSamplesResponse {
  samples: TitleSample[];
  total_files: number;
  titles_generated: number;
  generation_rate: number;    // 퍼센트
}
```

#### 15.4.2 matching-samples 응답 스키마

```typescript
interface MatchingSample {
  nas_file: {
    id: string;
    file_path: string;
    file_name: string;
  };
  sheet_row: {
    row_number: number;
    file_name: string;        // Sheet의 File Name 컬럼
    nas_folder_link: string;  // Sheet의 Nas Folder Link 컬럼
  };
  video_file: {
    id: string;
    display_title: string;
  };
  hand_clip: {
    id: string;
    timecode: string;
    hand_grade: string;
  };
  match_confidence: number;   // 0.0 ~ 1.0
}
```

### 15.5 검증 대시보드 (UI)

#### 15.5.1 제목 생성 검증 탭

```
┌─────────────────────────────────────────────────────────────────────┐
│  Title Generation Validation                    [Refresh] [Export]  │
├─────────────────────────────────────────────────────────────────────┤
│  Coverage: 1,263 / 1,429 files (88.4%)         ████████████░░ 88%   │
├─────────────────────────────────────────────────────────────────────┤
│ # │ 원본 파일명                │ display_title           │ Parser   │
│───│───────────────────────────│────────────────────────│──────────│
│ 1 │ 10-wsop-2024-be-ev-21... │ WSOP 2024 Event #21... │ Bracelet │
│ 2 │ WCLA24-15.mp4            │ 2024 WSOP Circuit LA...│ Circuit  │
│ 3 │ E05_GOG_final_edit...    │ Game of Gold E05...    │ GOG      │
│ 4 │ pad-s13-ep10-1234.mp4    │ PAD S13 Episode 10     │ PAD      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 15.5.2 NAS ↔ Sheets 매칭 탭

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAS ↔ Sheets Matching                          [Refresh] [Export]  │
├─────────────────────────────────────────────────────────────────────┤
│  Matched: 2,100 / 2,500 rows (84%)             ████████████░░ 84%   │
├─────────────────────────────────────────────────────────────────────┤
│ Sheet Row │ NAS File           │ VideoFile Title    │ Status     │
│───────────│───────────────────│───────────────────│────────────│
│ Row 15    │ WCLA24-15.mp4     │ WSOP-C LA #15     │ ✅ Matched │
│ Row 16    │ WCLA24-16.mp4     │ WSOP-C LA #16     │ ✅ Matched │
│ Row 17    │ (not found)       │ -                 │ ❌ Missing │
│ Row 18    │ event21-ft.mp4    │ WSOP 2024 #21 FT  │ ✅ Matched │
└─────────────────────────────────────────────────────────────────────┘
```

### 15.6 성공 기준 (추가)

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| Title Generation Rate | ≥ 95% | VideoFile with display_title / Total VideoFiles |
| NAS ↔ Sheets Match Rate | ≥ 90% | Matched HandClips / Total Sheet Rows |
| Catalog Coverage | ≥ 85% | VideoFiles with catalog_title / Total VideoFiles |
| Zero Empty Titles | 0 | VideoFiles where display_title = NULL or '' |

---

**문서 버전**: 1.2.0
**작성일**: 2025-12-11
**상태**: Active

### 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2025-12-11 | 초기 작성 - 전체 정보 통합 |
| 1.1.0 | 2025-12-11 | 핵심 목적 섹션, Contents API 추가 |
| 1.2.0 | 2025-12-11 | 데이터 매칭 검증 섹션 추가 (Section 15) |
