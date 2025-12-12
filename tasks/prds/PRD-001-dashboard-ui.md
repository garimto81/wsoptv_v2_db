# PRD-001: PokerVOD Data Quality Dashboard

**Version**: 2.1.0
**Status**: Phase 8 Complete - NAS 파일 정리 완료
**Created**: 2025-12-11
**Updated**: 2025-12-12
**Author**: Claude Code

---

## 1. 개요

### 1.1 프로젝트 목표

PokerVOD 백엔드의 **데이터 품질 모니터링 대시보드**를 개발합니다.

**핵심 목적 3가지:**
1. **NAS 폴더 분석 검증** - 21TB+ 스토리지의 1,415개 콘텐츠 파일이 제대로 스캔/파싱되었는지
2. **Google Sheets 동기화 검증** - 핸드 분석 데이터가 정확히 DB에 반영되었는지
3. **카탈로그 연결 무결성 검증** - NAS 파일 + Sheets 데이터가 올바르게 연결되었는지

> **Note**: 영상 재생 기능 없음. 순수 데이터 품질 모니터링 용도.

### 1.2 핵심 가치

| 가치 | 설명 |
|------|------|
| **데이터 무결성** | NAS ↔ VideoFile ↔ Episode ↔ HandClip 연결 상태 검증 |
| **파싱 정확도** | 파일명 파싱 성공/실패/미매칭 현황 추적 |
| **동기화 상태** | Google Sheets 동기화 진행률 및 오류 모니터링 |
| **문제 발견** | 미연결 파일, 파싱 실패, 중복 데이터 즉시 식별 |

### 1.3 기술 스택

| 영역 | 기술 | 버전 | 선택 이유 |
|------|------|------|----------|
| **Framework** | Next.js | 15.x | App Router, Server Components |
| **UI Library** | shadcn/ui | latest | 컴포넌트 복사 방식, 완전한 커스터마이징 |
| **Styling** | Tailwind CSS | 4.x | 유틸리티 우선, 일관된 디자인 |
| **State** | TanStack Query | 5.x | 서버 상태 캐싱, 자동 재검증 |
| **Charts** | Recharts | 2.x | React 친화적, 반응형 |
| **Icons** | Lucide React | latest | 일관된 아이콘 세트 |
| **Forms** | React Hook Form + Zod | latest | 타입 안전 폼 검증 |

---

## 2. 사용자 요구사항

### 2.1 Target User

| 사용자 | 역할 | 주요 작업 |
|--------|------|----------|
| **시스템 관리자** | 데이터 품질 검증 | NAS 스캔 검증, Sheets 동기화 확인, 연결 무결성 검사 |

### 2.2 User Stories

#### Epic 1: 데이터 품질 대시보드 (홈)
```
US-001: 관리자로서, 전체 데이터 품질 현황을 한눈에 볼 수 있어야 한다.
  - NAS 스캔 상태 (성공/실패/미처리)
  - Sheets 동기화 상태 (완료/진행중/에러)
  - 카탈로그 연결율 (NAS → VideoFile → Episode)
  - 문제 항목 개수 (빨간색 경고)

US-002: 관리자로서, 문제 항목을 클릭하면 상세 목록으로 이동할 수 있어야 한다.
  - 미연결 NAS 파일 → /nas/unlinked
  - 파싱 실패 파일 → /nas/failed
  - 동기화 에러 → /sync/errors
```

#### Epic 2: NAS 인벤토리 검증
```
US-003: 관리자로서, NAS 스캔 결과를 검증할 수 있어야 한다.
  - 전체 폴더/파일 수
  - 파싱 성공률 (파일명 → 메타데이터 추출)
  - 프로젝트별 인식률
  - 미인식 파일 목록

US-004: 관리자로서, VideoFile 연결 상태를 확인할 수 있어야 한다.
  - NASFile → VideoFile 연결된 파일 수
  - 미연결 파일 목록 (연결 필요)
  - 중복 의심 파일 목록

US-005: 관리자로서, 파일명 파싱 결과를 검토할 수 있어야 한다.
  - 파서별 매칭 통계 (WSOP, HCL, GGMillions 등)
  - 파싱 실패 파일 목록 + 원인
  - 수동 연결 기능
```

#### Epic 3: Google Sheets 동기화 검증
```
US-006: 관리자로서, Sheets 동기화 상태를 확인할 수 있어야 한다.
  - 시트별 동기화 진행률 (행 수 기준)
  - 마지막 동기화 시간
  - 에러 발생 행 목록

US-007: 관리자로서, HandClip 생성 결과를 검증할 수 있어야 한다.
  - 총 생성된 HandClip 수
  - VideoFile 연결된 클립 수
  - 미연결 클립 목록 (연결 필요)

US-008: 관리자로서, 수동 동기화를 실행할 수 있어야 한다.
  - 시트 선택 → 동기화 시작
  - 실시간 진행 상황
  - 결과 요약 (생성/스킵/에러)
```

#### Epic 4: 카탈로그 연결 검증
```
US-009: 관리자로서, 전체 데이터 연결 무결성을 확인할 수 있어야 한다.
  - Project → Season → Event → Episode 계층 구조 검증
  - Episode ↔ VideoFile 연결 상태
  - VideoFile ↔ NASFile 연결 상태
  - HandClip ↔ Episode/VideoFile 연결 상태

US-010: 관리자로서, 고아(Orphan) 레코드를 식별할 수 있어야 한다.
  - Episode 없는 VideoFile
  - VideoFile 없는 HandClip
  - 연결되지 않은 NASFile
  - 각 목록에서 수동 연결 가능

US-011: 관리자로서, 연결 통계를 차트로 볼 수 있어야 한다.
  - 프로젝트별 연결율 (바 차트)
  - 연결 상태 분포 (파이 차트: 완전연결/부분연결/미연결)
```

---

## 3. 정보 아키텍처

### 3.1 사이트맵

```
/
├── /                       # 데이터 품질 대시보드 (홈)
│   ├── NAS 스캔 상태 카드
│   ├── Sheets 동기화 상태 카드
│   ├── 카탈로그 연결율 카드
│   └── 문제 항목 경고
│
├── /nas                    # NAS 인벤토리 검증
│   ├── /nas                # NAS 전체 통계
│   ├── /nas/folders        # 폴더 목록 (트리 뷰)
│   ├── /nas/files          # 파일 목록
│   ├── /nas/unlinked       # 미연결 파일 목록
│   ├── /nas/failed         # 파싱 실패 파일
│   └── /nas/duplicates     # 중복 의심 파일
│
├── /sync                   # Sheets 동기화 검증
│   ├── /sync               # 동기화 상태 요약
│   ├── /sync/sheets        # 시트별 상태
│   ├── /sync/clips         # HandClip 검증
│   ├── /sync/errors        # 동기화 에러 목록
│   └── /sync/history       # 동기화 히스토리
│
├── /catalog                # 카탈로그 연결 검증
│   ├── /catalog            # 연결 무결성 요약
│   ├── /catalog/hierarchy  # 계층 구조 검증
│   ├── /catalog/orphans    # 고아 레코드 목록
│   └── /catalog/stats      # 연결 통계 차트
│
└── /actions                # 수동 작업 (향후)
    ├── /actions/link       # 수동 연결
    └── /actions/rescan     # 재스캔 실행
```

### 3.2 네비게이션 구조

```
┌────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard   NAS검증   Sheets검증   카탈로그검증       │
│                                                        [Refresh]
└────────────────────────────────────────────────────────────────┘
```

---

## 4. 화면 설계

### 4.1 데이터 품질 대시보드 (홈)

#### 레이아웃
```
┌─────────────────────────────────────────────────────────────────┐
│  PokerVOD Data Quality Dashboard                     [Refresh]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┬─────────────────┬─────────────────────────┐│
│  │ NAS 스캔 상태    │ Sheets 동기화    │ 카탈로그 연결율          ││
│  │                 │                 │                         ││
│  │ ✓ 1,912 파일   │ ✓ 2,300 행     │ 연결됨: 1,750 (91%)    ││
│  │ ⚠ 12 미연결    │ ⚠ 5 에러       │ 미연결: 162 (9%)       ││
│  │ ✗ 3 파싱실패   │ 마지막: 2시간전  │                         ││
│  │                 │                 │ [████████░░] 91%       ││
│  │ [상세보기]       │ [상세보기]       │ [상세보기]               ││
│  └─────────────────┴─────────────────┴─────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ⚠ 문제 항목 요약                              총 20개 문제   ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │ 🔴 미연결 NAS 파일         12개    [목록 보기 →]             ││
│  │    VideoFile과 연결되지 않은 비디오 파일                     ││
│  │                                                             ││
│  │ 🔴 파싱 실패 파일          3개     [목록 보기 →]             ││
│  │    파일명에서 메타데이터 추출 실패                           ││
│  │                                                             ││
│  │ 🟡 Sheets 동기화 에러      5개     [목록 보기 →]             ││
│  │    특정 행 처리 중 오류 발생                                 ││
│  │                                                             ││
│  │ 🟡 고아 HandClip           0개     [목록 보기 →]             ││
│  │    VideoFile/Episode 연결 없는 클립                         ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────┬──────────────────────────────────┐│
│  │ 프로젝트별 파싱 현황       │ 연결 상태 분포                    ││
│  │                          │                                  ││
│  │ WSOP      ███████ 95%   │      ┌──────┐                    ││
│  │ HCL       ██████  92%   │   ┌──┤ 91%  ├──┐                 ││
│  │ GGMillions █████   88%   │   │  │연결됨│  │                 ││
│  │ MPP       ████    85%   │   │  └──────┘  │                 ││
│  │ PAD       ████    84%   │   │  미연결 9% │                 ││
│  │ GOG       ███     80%   │   └────────────┘                 ││
│  │ OTHER     ██      65%   │                                  ││
│  └──────────────────────────┴──────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 컴포넌트
| 컴포넌트 | 데이터 소스 | 새로고침 |
|---------|------------|---------|
| `NASStatusCard` | `/api/v1/nas/files/stats` | 5분 |
| `SyncStatusCard` | `/api/v1/sync/summary` | 1분 |
| `LinkageStatusCard` | 커스텀 집계 API 필요 | 5분 |
| `ProblemSummary` | 각 문제 유형 count | 1분 |
| `ProjectParsingChart` | 파서별 통계 API 필요 | 10분 |
| `LinkageDistribution` | 연결 상태 집계 | 5분 |

### 4.2 NAS 인벤토리 검증 (/nas)

#### 레이아웃
```
┌─────────────────────────────────────────────────────────────────┐
│  NAS 인벤토리 검증                                    [재스캔]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [전체] [미연결] [파싱실패] [중복의심]                           │
│                                                                  │
│  ┌────────────┬────────────┬────────────┬────────────┐         │
│  │ 전체 파일   │ 연결됨     │ 미연결      │ 파싱실패    │         │
│  │ 1,912     │ 1,750     │ 12        │ 3         │         │
│  │           │ (91.5%)   │ (0.6%)    │ (0.2%)    │         │
│  └────────────┴────────────┴────────────┴────────────┘         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 파일 목록                                      정렬: 최신순 ▼││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │ 📁 /nas/WSOP/2024/Event_05/                                ││
│  │ ├─ 🔴 wsop_2024_ev05_day1_unknown.mp4     [미연결] [연결]  ││
│  │ │      파싱: 실패 (패턴 미매칭)                              ││
│  │ │      크기: 12.5 GB | 수정: 2024-12-01                    ││
│  │ │                                                           ││
│  │ ├─ ✓  05-wsop-2024-be-ev-05-day2-ft.mp4   [연결됨]         ││
│  │ │      → VideoFile: WSOP 2024 Event #5 Final Table         ││
│  │ │      → Episode: Day 2 Final Table                        ││
│  │ │      크기: 15.2 GB | 수정: 2024-12-01                    ││
│  │ │                                                           ││
│  │ └─ 🟡 05-wsop-2024-be-ev-05-day2-ft_copy.mp4 [중복의심]    ││
│  │        유사파일: 05-wsop-2024-be-ev-05-day2-ft.mp4          ││
│  │        크기: 15.2 GB | 수정: 2024-12-02                    ││
│  │                                                             ││
│  │ [더 보기...]                                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────┬──────────────────────────────────┐│
│  │ 파서별 매칭 통계          │ 파일 카테고리 분포                ││
│  │                          │                                  ││
│  │ WSOPBracelet  ████ 450  │ Video     ████████ 1800         ││
│  │ WSOPCircuit   ███  320  │ Metadata  ██       80           ││
│  │ HCL           ███  280  │ System    █        20           ││
│  │ GGMillions    ██   180  │ Archive   █        10           ││
│  │ 미매칭        █    162  │ Other     █        2            ││
│  └──────────────────────────┴──────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 컴포넌트
| 컴포넌트 | 기능 |
|---------|------|
| `StatusTabs` | 전체/미연결/파싱실패/중복 탭 |
| `StatCards` | 파일 상태별 카운트 |
| `FileList` | 파일 목록 (트리 뷰) |
| `FileRow` | 파일 상태, 연결 정보, 액션 |
| `ParserStats` | 파서별 매칭 통계 차트 |
| `CategoryChart` | 파일 카테고리 분포 |

### 4.3 Sheets 동기화 검증 (/sync)

#### 레이아웃
```
┌─────────────────────────────────────────────────────────────────┐
│  Sheets 동기화 검증                              [전체 동기화]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [동기화 상태] [HandClip 검증] [에러 목록] [히스토리]            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Google Sheets 동기화 상태                                   ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │ METADATA_ARCHIVE                              [동기화 실행]  ││
│  │ ┌───────────────────────────────────────────┐              ││
│  │ │ ████████████████████░░░░░░░░░░░░░░░░░░░░ │ 90%          ││
│  │ └───────────────────────────────────────────┘              ││
│  │ 동기화 행: 1,500 / 1,667  |  마지막: 2025-12-11 10:30      ││
│  │ 생성: 1,450  |  스킵: 45  |  에러: 5                        ││
│  │                                                             ││
│  │ ICONIK_METADATA                               [동기화 실행]  ││
│  │ ┌───────────────────────────────────────────┐              ││
│  │ │ ████████████████████████████████████████ │ 100%         ││
│  │ └───────────────────────────────────────────┘              ││
│  │ 동기화 행: 800 / 800  |  마지막: 2025-12-11 11:00          ││
│  │ 생성: 790  |  스킵: 10  |  에러: 0                          ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ HandClip 연결 상태 검증                                      ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │ 총 HandClip: 2,240                                          ││
│  │ ├─ ✓ VideoFile 연결됨: 2,100 (94%)                         ││
│  │ ├─ ✓ Episode 연결됨: 2,050 (92%)                           ││
│  │ ├─ 🟡 VideoFile만 연결: 50 (2%)                            ││
│  │ └─ 🔴 미연결 (고아): 40 (2%)           [목록 보기 →]        ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 동기화 에러 목록 (최근 5개)                   [전체 보기 →]   ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ Row 1523: Player 'Unknown Player' not found                 ││
│  │ Row 1489: Invalid timecode format '25:99:00'                ││
│  │ Row 1456: Duplicate entry (sheet_source, row_number)        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 컴포넌트
| 컴포넌트 | 기능 |
|---------|------|
| `SyncStatusCard` | 시트별 동기화 진행률 |
| `HandClipLinkage` | 클립 연결 상태 요약 |
| `SyncErrorList` | 에러 행 목록 |
| `SyncHistory` | 동기화 히스토리 테이블 |

### 4.4 카탈로그 연결 검증 (/catalog)

#### 레이아웃
```
┌─────────────────────────────────────────────────────────────────┐
│  카탈로그 연결 검증                                   [새로고침]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [연결 요약] [계층 구조] [고아 레코드] [연결 통계]                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 데이터 연결 무결성 요약                                       ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │  ┌────────────┬────────────┬────────────┬────────────┐     ││
│  │  │ NASFile    │ VideoFile  │ Episode    │ HandClip   │     ││
│  │  │ 1,912      │ 1,750      │ 320        │ 2,240      │     ││
│  │  └─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┘     ││
│  │        │    91%     │    94%     │    89%     │            ││
│  │        ▼            ▼            ▼            ▼            ││
│  │  [연결됨 1,750] [연결됨 1,645] [연결됨 285] [연결됨 1,995]  ││
│  │  [미연결  162] [미연결  105] [미연결  35] [미연결  245]    ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 계층 구조 검증 (Project → Season → Event → Episode)         ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │ 📁 WSOP (2018-2024)                              [펼치기]   ││
│  │ │  Seasons: 7 | Events: 456 | Episodes: 1,280              ││
│  │ │  연결율: ████████████████░░░░ 85%                        ││
│  │ │  🔴 미연결 Episode: 192개                                 ││
│  │ │                                                           ││
│  │ 📁 HCL (2022-2024)                               [펼치기]   ││
│  │ │  Seasons: 3 | Events: 45 | Episodes: 180                 ││
│  │ │  연결율: ██████████████████░░ 92%                        ││
│  │ │  ✓ 연결 양호                                             ││
│  │ │                                                           ││
│  │ 📁 GGMillions (2023-2024)                        [펼치기]   ││
│  │ │  Seasons: 2 | Events: 24 | Episodes: 96                  ││
│  │ │  연결율: ██████████████████░░ 88%                        ││
│  │ │  🟡 미연결 Episode: 12개                                  ││
│  │ │                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 고아(Orphan) 레코드 목록                      총 547개 문제  ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │ 🔴 Episode 없는 VideoFile                      105개        ││
│  │    "2024_wsop_ev_12_final.mp4" - Episode 연결 필요          ││
│  │    "hcl_s3_ep_bonus.mp4" - Episode 매칭 실패               ││
│  │                                     [전체 목록 →] [일괄연결] ││
│  │                                                             ││
│  │ 🔴 VideoFile 없는 HandClip                     245개        ││
│  │    Row 1523: "Phil Ivey vs Tom Dwan" - 타임코드만 존재      ││
│  │    Row 1489: "Epic River Bluff" - VideoFile 미매칭          ││
│  │                                     [전체 목록 →] [일괄연결] ││
│  │                                                             ││
│  │ 🟡 연결 없는 NASFile                           162개        ││
│  │    /nas/WSOP/2024/unknown/ 폴더 내 파일 다수               ││
│  │                                     [전체 목록 →] [파싱재시도]││
│  │                                                             ││
│  │ 🟡 HandClip 없는 Episode                       35개         ││
│  │    WSOP 2024 Day1-Day3 에피소드 (Sheets 동기화 필요)        ││
│  │                                     [전체 목록 →] [동기화]   ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────┬──────────────────────────────────┐│
│  │ 프로젝트별 연결율          │ 연결 상태 분포                    ││
│  │                          │                                  ││
│  │ HCL       ██████████ 92% │      ┌──────────┐               ││
│  │ GGMillions ████████░ 88% │   ┌──┤ 완전연결  ├──┐            ││
│  │ WSOP      ████████░ 85% │   │  │   78%   │  │            ││
│  │ MPP       ███████░░ 80% │   │  └──────────┘  │            ││
│  │ PAD       ██████░░░ 75% │   │ 부분연결 15%   │            ││
│  │ GOG       █████░░░░ 70% │   │ 미연결 7%      │            ││
│  │ OTHER     ███░░░░░░ 55% │   └───────────────┘            ││
│  └──────────────────────────┴──────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 컴포넌트
| 컴포넌트 | 기능 |
|---------|------|
| `LinkageOverview` | 4개 엔티티 연결 상태 요약 |
| `HierarchyTree` | Project → Episode 계층 구조 (접기/펼치기) |
| `OrphanList` | 고아 레코드 유형별 목록 |
| `LinkageChart` | 프로젝트별 연결율 바 차트 |
| `LinkageDistribution` | 연결 상태 파이 차트 |
| `BulkLinkAction` | 일괄 연결 모달 |

---

## 5. 디자인 시스템

### 5.1 컬러 팔레트

```css
/* Primary - 포커 그린 테마 */
--primary-50:  #f0fdf4;
--primary-100: #dcfce7;
--primary-500: #22c55e;
--primary-600: #16a34a;
--primary-700: #15803d;
--primary-900: #14532d;

/* Secondary - 골드 악센트 */
--secondary-500: #eab308;
--secondary-600: #ca8a04;

/* Neutral - 다크 모드 기본 */
--neutral-50:  #fafafa;
--neutral-100: #f4f4f5;
--neutral-200: #e4e4e7;
--neutral-700: #3f3f46;
--neutral-800: #27272a;
--neutral-900: #18181b;
--neutral-950: #09090b;

/* Semantic */
--success: #22c55e;
--warning: #f59e0b;
--error:   #ef4444;
--info:    #3b82f6;
```

### 5.2 타이포그래피

```css
/* Font Family */
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* Font Sizes */
--text-xs:   0.75rem;   /* 12px */
--text-sm:   0.875rem;  /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg:   1.125rem;  /* 18px */
--text-xl:   1.25rem;   /* 20px */
--text-2xl:  1.5rem;    /* 24px */
--text-3xl:  1.875rem;  /* 30px */
--text-4xl:  2.25rem;   /* 36px */

/* Font Weights */
--font-normal:   400;
--font-medium:   500;
--font-semibold: 600;
--font-bold:     700;
```

### 5.3 스페이싱

```css
/* 4px 기반 스케일 */
--space-1:  0.25rem;  /* 4px */
--space-2:  0.5rem;   /* 8px */
--space-3:  0.75rem;  /* 12px */
--space-4:  1rem;     /* 16px */
--space-5:  1.25rem;  /* 20px */
--space-6:  1.5rem;   /* 24px */
--space-8:  2rem;     /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### 5.4 컴포넌트 변형

#### Button
```tsx
<Button variant="default">Primary Action</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Delete</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
```

#### Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```

#### Badge
```tsx
<Badge variant="default">Default</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="outline">Outline</Badge>
<Badge variant="destructive">Error</Badge>
```

### 5.5 다크 모드 (기본)

대시보드는 기본적으로 다크 모드를 사용합니다:

```css
:root {
  --background: #09090b;
  --foreground: #fafafa;
  --card: #18181b;
  --card-foreground: #fafafa;
  --border: #27272a;
  --input: #27272a;
  --ring: #22c55e;
}
```

---

## 6. API 연동

### 6.1 API 엔드포인트 매핑

| 화면 | API 엔드포인트 | Method | 설명 |
|------|---------------|--------|------|
| **데이터 품질 대시보드** | | | |
| NAS 스캔 상태 | `/api/v1/nas/files/stats` | GET | 파일 상태별 카운트 |
| Sheets 동기화 상태 | `/api/v1/sync/summary` | GET | 동기화 진행률/에러 |
| 카탈로그 연결율 | `/api/v1/quality/linkage-stats` | GET | **신규** - 연결 무결성 통계 |
| 문제 항목 카운트 | `/api/v1/quality/problems` | GET | **신규** - 문제 유형별 카운트 |
| **NAS 인벤토리 검증** | | | |
| 파일 목록 | `/api/v1/nas/files?status=` | GET | 상태 필터링 (linked/unlinked/failed) |
| 폴더 트리 | `/api/v1/nas/folders` | GET | 폴더 구조 |
| 파서별 통계 | `/api/v1/nas/parser-stats` | GET | **신규** - 파서 매칭 통계 |
| 중복 의심 파일 | `/api/v1/nas/duplicates` | GET | **신규** - 중복 감지 |
| 수동 연결 | `/api/v1/nas/files/{id}/link` | POST | **신규** - VideoFile 연결 |
| **Sheets 동기화 검증** | | | |
| 시트별 상태 | `/api/v1/sync/records` | GET | 시트별 동기화 상태 |
| 동기화 실행 | `/api/v1/sync/start` | POST | 수동 동기화 시작 |
| 에러 목록 | `/api/v1/sync/errors` | GET | **신규** - 동기화 에러 |
| HandClip 연결 상태 | `/api/v1/hand-clips/linkage-stats` | GET | **신규** - 클립 연결 통계 |
| **카탈로그 연결 검증** | | | |
| 계층 구조 | `/api/v1/projects?include=stats` | GET | 프로젝트별 연결 통계 |
| 고아 레코드 | `/api/v1/quality/orphans` | GET | **신규** - 고아 레코드 목록 |
| 일괄 연결 | `/api/v1/quality/bulk-link` | POST | **신규** - 일괄 연결 작업 |
| 연결율 차트 | `/api/v1/quality/linkage-by-project` | GET | **신규** - 프로젝트별 연결율 |

### 6.2 TanStack Query 설정

```typescript
// lib/api.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5분
      gcTime: 10 * 60 * 1000,   // 10분
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// hooks/useNASStats.ts
export function useNASStats() {
  return useQuery({
    queryKey: ['nas', 'stats'],
    queryFn: () => api.get('/api/v1/nas/files/stats'),
    refetchInterval: 5 * 60 * 1000, // 5분마다 갱신
  });
}

// hooks/useSyncStatus.ts
export function useSyncStatus() {
  return useQuery({
    queryKey: ['sync', 'summary'],
    queryFn: () => api.get('/api/v1/sync/summary'),
    refetchInterval: 60 * 1000, // 1분마다 갱신
  });
}

// hooks/useLinkageStats.ts
export function useLinkageStats() {
  return useQuery({
    queryKey: ['quality', 'linkage'],
    queryFn: () => api.get('/api/v1/quality/linkage-stats'),
    refetchInterval: 5 * 60 * 1000, // 5분마다 갱신
  });
}

// hooks/useProblems.ts
export function useProblems() {
  return useQuery({
    queryKey: ['quality', 'problems'],
    queryFn: () => api.get('/api/v1/quality/problems'),
    refetchInterval: 60 * 1000, // 1분마다 갱신
  });
}

// hooks/useOrphans.ts
export function useOrphans(type?: 'video_file' | 'hand_clip' | 'nas_file' | 'episode') {
  return useQuery({
    queryKey: ['quality', 'orphans', type],
    queryFn: () => api.get('/api/v1/quality/orphans', { params: { type } }),
  });
}
```

---

## 7. 개발 계획

### 7.1 마일스톤

| Phase | 산출물 | 상태 |
|-------|--------|------|
| **Phase 1: 기반 구축** | Next.js 15 프로젝트, shadcn/ui 설치, 라우팅, API 클라이언트 | ✅ 완료 |
| **Phase 2: 데이터 품질 대시보드** | 홈 화면, 상태 카드 3종, 문제 항목 요약, 차트 | ✅ 완료 |
| **Phase 3: NAS 인벤토리 검증** | 파일 목록, 상태 탭, 파서 통계 | ✅ 완료 |
| **Phase 4: Sheets 동기화 검증** | 시트별 진행률, HandClip 연결 상태, 에러 목록 | ✅ 완료 |
| **Phase 5: 카탈로그 연결 검증** | 고아 레코드 목록, 연결율 차트 | ✅ 완료 |
| **Phase 6: 품질 API 개발** | 신규 API 엔드포인트 10개 (백엔드 작업) | ✅ 완료 |
| **Phase 7: Frontend 개발** | Next.js 16 + shadcn/ui + TanStack Query | ✅ 완료 |
| **Phase 8: Docker 배포 + NAS 정리** | Docker Compose, NAS 파일 제외 시스템 | ✅ 완료 |

### 7.2 신규 API 엔드포인트 (백엔드 필요)

| 엔드포인트 | 설명 | 우선순위 |
|-----------|------|---------|
| `GET /api/v1/quality/linkage-stats` | 전체 연결 무결성 통계 | 높음 |
| `GET /api/v1/quality/problems` | 문제 유형별 카운트 | 높음 |
| `GET /api/v1/quality/orphans` | 고아 레코드 목록 | 높음 |
| `GET /api/v1/quality/linkage-by-project` | 프로젝트별 연결율 | 중간 |
| `POST /api/v1/quality/bulk-link` | 일괄 연결 작업 | 중간 |
| `GET /api/v1/nas/parser-stats` | 파서별 매칭 통계 | 높음 |
| `GET /api/v1/nas/duplicates` | 중복 의심 파일 | 낮음 |
| `POST /api/v1/nas/files/{id}/link` | 수동 VideoFile 연결 | 중간 |
| `GET /api/v1/sync/errors` | 동기화 에러 목록 | 높음 |
| `GET /api/v1/hand-clips/linkage-stats` | HandClip 연결 통계 | 중간 |

### 7.3 폴더 구조

```
frontend/
├── app/
│   ├── page.tsx                  # / 데이터 품질 대시보드 (홈)
│   ├── nas/
│   │   ├── page.tsx              # /nas NAS 인벤토리 검증
│   │   ├── unlinked/page.tsx     # /nas/unlinked 미연결 파일
│   │   ├── failed/page.tsx       # /nas/failed 파싱 실패
│   │   └── duplicates/page.tsx   # /nas/duplicates 중복 의심
│   ├── sync/
│   │   ├── page.tsx              # /sync 동기화 상태
│   │   ├── clips/page.tsx        # /sync/clips HandClip 검증
│   │   ├── errors/page.tsx       # /sync/errors 에러 목록
│   │   └── history/page.tsx      # /sync/history 히스토리
│   ├── catalog/
│   │   ├── page.tsx              # /catalog 연결 무결성 요약
│   │   ├── hierarchy/page.tsx    # /catalog/hierarchy 계층 구조
│   │   ├── orphans/page.tsx      # /catalog/orphans 고아 레코드
│   │   └── stats/page.tsx        # /catalog/stats 연결 통계
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/                       # shadcn/ui 컴포넌트
│   ├── dashboard/
│   │   ├── nas-status-card.tsx
│   │   ├── sync-status-card.tsx
│   │   ├── linkage-status-card.tsx
│   │   ├── problem-summary.tsx
│   │   └── linkage-charts.tsx
│   ├── nas/
│   │   ├── file-list.tsx
│   │   ├── file-row.tsx
│   │   ├── parser-stats.tsx
│   │   └── link-modal.tsx
│   ├── sync/
│   │   ├── sheet-progress.tsx
│   │   ├── handclip-linkage.tsx
│   │   └── error-list.tsx
│   ├── catalog/
│   │   ├── hierarchy-tree.tsx
│   │   ├── orphan-list.tsx
│   │   ├── linkage-chart.tsx
│   │   └── bulk-link-modal.tsx
│   └── layout/
│       ├── header.tsx
│       ├── sidebar.tsx
│       └── nav-link.tsx
├── hooks/
│   ├── use-nas-stats.ts
│   ├── use-sync-status.ts
│   ├── use-linkage-stats.ts
│   ├── use-problems.ts
│   └── use-orphans.ts
├── lib/
│   ├── api.ts                    # API 클라이언트
│   ├── query-client.ts
│   └── utils.ts
└── types/
    ├── nas.ts
    ├── sync.ts
    ├── quality.ts
    └── linkage.ts
```

---

## 8. 성공 지표

### 8.1 데이터 품질 목표

| 지표 | 현재 | 목표 | 설명 |
|------|------|------|------|
| NAS 파싱 성공률 | 측정 필요 | > 95% | 파일명 → 메타데이터 추출 |
| Sheets 동기화 성공률 | 측정 필요 | > 98% | 행 단위 동기화 |
| 카탈로그 연결율 | 측정 필요 | > 90% | NAS → VideoFile → Episode |
| 고아 레코드 | 측정 필요 | < 5% | 미연결 데이터 비율 |

### 8.2 기능 완성도

| 지표 | 목표 |
|------|------|
| 화면 구현 | 4개 주요 화면 (홈, NAS, Sync, Catalog) |
| API 연동 | 기존 API + 신규 10개 엔드포인트 |
| 반응형 | Desktop 우선 (1280px+) |

### 8.3 성능 지표

| 지표 | 목표 |
|------|------|
| First Contentful Paint | < 1.5s |
| Largest Contentful Paint | < 2.5s |
| API 응답 시간 | < 500ms (집계 쿼리) |
| 대시보드 새로고침 | < 1s |

---

## 9. 부록

### 9.1 데이터 모델 참조

```
NASFile (1,415개 콘텐츠 파일)
    ├─ video (1,291개)
    │   ├─ linked: 1,260개 (97.6%)
    │   └─ excluded: 31개 (Clips/Player Emotion)
    ├─ system (122개)
    ├─ metadata (1개)
    └─ archive (1개)

VideoFile (1,260개)
    ↓ episode_id
Episode (58개)
    ↓ event_id
Event → Season → Project

HandClip (동기화 예정)
    ↓ video_file_id
VideoFile
    ↓ episode_id
Episode
```

### 9.1.1 NAS 파일 통계 (2025-12-12)

| 구분 | 개수 | 설명 |
|------|------|------|
| Windows 탐색기 표시 | 1,948 | 폴더 198개 포함 |
| macOS 시스템 파일 | 519 | `.DS_Store`, `._*` (제외) |
| Windows 시스템 파일 | 14 | `Thumbs.db` (제외) |
| **DB 저장 콘텐츠 파일** | **1,415** | 실제 관리 대상 |

### 9.1.2 비디오 파일 연결률

| 항목 | 값 |
|------|-----|
| 전체 비디오 | 1,291개 |
| 제외 대상 | 31개 (Clips 17, Player Emotion 14) |
| 카탈로그 대상 | 1,260개 |
| **연결 완료** | **1,260개 (100%)** |

### 9.2 파서 매핑

| 파서 | 패턴 예시 | 프로젝트 |
|------|----------|---------|
| WSOPBracelet | `05-wsop-2024-be-ev-05-day2-ft.mp4` | WSOP |
| WSOPCircuit | `WSOPTX_2024_Event_01_Day1.mp4` | WSOP Circuit |
| HCL | `HCL_S3_EP15_720p.mp4` | Hustler Casino Live |
| GGMillions | `GGM_2024_W1_Day2_Final.mp4` | GGMillions |

### 9.3 참조 디자인

- [shadcn/ui Dashboard Example](https://ui.shadcn.com/examples/dashboard)
- [Vercel Dashboard](https://vercel.com/dashboard) - 상태 모니터링 참고

### 9.4 관련 문서

- `backend/src/api/v1/` - 기존 API 엔드포인트
- `backend/src/services/nas_inventory/` - NAS 스캔 서비스
- `backend/src/services/sheets_sync/` - Sheets 동기화 서비스
- `backend/src/models/` - 데이터 모델 정의

---

## 10. Phase 8: Docker 배포 설정

### 10.1 개요

개발 환경과 프로덕션 환경의 일관성을 보장하기 위해 Docker Compose 기반 배포를 구현합니다.

### 10.2 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
├─────────────────┬─────────────────┬─────────────────────┤
│   Frontend      │    Backend      │     Database        │
│   (Next.js)     │    (FastAPI)    │   (PostgreSQL)      │
│   Port 3000     │    Port 8000    │   Port 5432         │
└─────────────────┴─────────────────┴─────────────────────┘
```

### 10.3 컨테이너 구성

| 서비스 | 이미지 | 포트 | 설명 |
|--------|--------|------|------|
| `frontend` | Node.js 20 Alpine | 3000 | Next.js 프로덕션 서버 |
| `backend` | Python 3.12 Slim | 8000 | FastAPI + Uvicorn |
| `postgres` | PostgreSQL 16 Alpine | 5432 | 데이터베이스 |

### 10.4 Dockerfile 전략

#### Frontend (Multi-stage Build)
```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
# Install dependencies only

# Stage 2: Builder
FROM node:20-alpine AS builder
# Build Next.js application

# Stage 3: Runner
FROM node:20-alpine AS runner
# Production-optimized runtime
```

#### Backend
```dockerfile
FROM python:3.12-slim
# Install dependencies via pip
# Run with uvicorn
```

### 10.5 환경 변수

| 변수 | 개발 | 프로덕션 |
|------|------|---------|
| `DATABASE_URL` | `postgresql://...@localhost:5432/pokervod` | `postgresql://...@postgres:5432/pokervod` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | `http://backend:8000` |
| `NODE_ENV` | `development` | `production` |

### 10.6 실행 명령어

```bash
# 개발 환경
docker compose up -d

# 프로덕션 빌드
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 로그 확인
docker compose logs -f

# 종료
docker compose down
```

### 10.7 산출물

| 파일 | 위치 | 설명 |
|------|------|------|
| `Dockerfile` | `frontend/` | Next.js 멀티스테이지 빌드 |
| `Dockerfile` | `backend/` | FastAPI 컨테이너 |
| `docker-compose.yml` | 프로젝트 루트 | 전체 스택 오케스트레이션 |
| `.env.example` | 프로젝트 루트 | 환경 변수 템플릿 |
| `.dockerignore` | 각 서비스 | 빌드 제외 파일 |

---

**문서 끝**
