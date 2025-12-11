# PRD: 블럭 A - NAS Inventory Agent

> **버전**: 1.0.0 | **작성일**: 2025-12-11 | **블럭 코드**: A

---

## 1. 개요

### 1.1 목적

NAS 스토리지(19TB+)의 영상 파일을 스캔하고, 프로젝트별 파일명 패턴을 파싱하여 메타데이터를 추출합니다.

### 1.2 책임 범위

| 항목 | 포함 | 제외 |
|------|------|------|
| NAS 트리 스캔 | O | |
| 파일 메타데이터 추출 | O | |
| 파일명 파싱 (7패턴) | O | |
| 버전 타입 분류 | O | |
| 카탈로그 구조 정의 | | X (블럭 B) |
| 핸드 분석 | | X (블럭 C) |

---

## 2. 데이터 소스

### 2.1 NAS 경로

```
\\10.10.100.122\docker\GGPNAs\ARCHIVE
```

### 2.2 프로젝트별 폴더 구조

| 프로젝트 | 경로 | 파일 수 | 용량 |
|----------|------|---------|------|
| WSOP | `/WSOP/` | 1,279 | ~18TB |
| PAD | `/PAD/` | 45 | ~200GB |
| GOG | `/GOG 최종/` | 24 | ~50GB |
| GGMillions | `/GGMillions/` | 13 | ~100GB |
| MPP | `/MPP/` | 11 | ~100GB |
| HCL | `/HCL/` | 1 | 준비중 |

**총계**: 1,373 영상 + 518 메타데이터 + 14 시스템 파일

---

## 3. 파일 파서 시스템

### 3.1 파서 팩토리

```python
class ParserFactory:
    @staticmethod
    def get_parser(file_path: str) -> BaseParser:
        if "wsop" in file_path.lower() and "-be-ev-" in file_path:
            return WSOPBraceletParser()
        elif "WCLA" in file_path:
            return WSOPCircuitParser()
        elif "wsop" in file_path.lower() and "ARCHIVE" in file_path:
            return WSOPArchiveParser()
        elif "GGMillions" in file_path:
            return GGMillionsParser()
        elif "GOG" in file_path:
            return GOGParser()
        elif "PAD" in file_path:
            return PADParser()
        elif "MPP" in file_path:
            return MPPParser()
        else:
            return GenericParser()
```

### 3.2 7가지 파싱 패턴

#### 패턴 1: WSOP Bracelet

```
{번호}-wsop-{연도}-be-ev-{이벤트}-{바이인}-{게임}-{추가정보}.mp4

예시: 10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten-reclaims-chip-lead.mp4
```

**추출 필드**:
| 필드 | 예시 값 | DB 컬럼 |
|------|---------|---------|
| clip_number | 10 | `video_files.display_order` |
| year | 2024 | `seasons.year` |
| event_number | 21 | `events.event_number` |
| buy_in | 25k | `events.buy_in` |
| game_type | nlh | `events.game_type` |
| table_type | ft | `episodes.table_type` |

#### 패턴 2: WSOP Circuit

```
WCLA{YY}-{번호}.mp4

예시: WCLA24-15.mp4
```

**추출 필드**:
| 필드 | 예시 값 |
|------|---------|
| year | 2024 |
| clip_number | 15 |

#### 패턴 3: WSOP Archive (PRE-2016)

```
wsop-{연도}-me-{버전}.mp4

예시: wsop-1973-me-nobug.mp4
```

**추출 필드**:
| 필드 | 예시 값 |
|------|---------|
| year | 1973 |
| event_type | me (Main Event) |
| version_type | nobug |

#### 패턴 4: GGMillions

```
{YYMMDD}_Super High Roller Poker FINAL TABLE with {플레이어}.mp4
Super High Roller Poker FINAL TABLE with {플레이어}.mp4

예시: 250507_Super High Roller Poker FINAL TABLE with Joey ingram.mp4
```

**추출 필드**:
| 필드 | 예시 값 |
|------|---------|
| date | 2025-05-07 |
| featured_player | Joey ingram |
| table_type | final_table |

#### 패턴 5: GOG

```
E{번호}_GOG_final_edit_{YYYYMMDD}[_수정].mp4
E{번호}_GOG_final_edit_클린본_{YYYYMMDD}.mp4

예시: E01_GOG_final_edit_231106.mp4
```

**추출 필드**:
| 필드 | 예시 값 |
|------|---------|
| episode_number | 1 |
| version_type | final_edit 또는 clean |
| edit_date | 2023-11-06 |

#### 패턴 6: PAD

```
pad-s{시즌}-ep{에피소드}-{코드}.mp4
PAD_S{시즌}_EP{에피소드}_{버전}-{코드}.mp4

예시: pad-s12-ep01-12345.mp4
```

**추출 필드**:
| 필드 | 예시 값 |
|------|---------|
| season_number | 12 |
| episode_number | 1 |
| version_code | 12345 |

#### 패턴 7: MPP

```
${GTD금액} GTD   ${바이인} {이벤트명} ? {Day/Final}.mp4

예시: $1M GTD   $1K PokerOK Mystery Bounty ? Day 1A.mp4
```

**추출 필드**:
| 필드 | 예시 값 |
|------|---------|
| gtd_amount | 1000000 |
| buy_in | 1000 |
| event_name | PokerOK Mystery Bounty |
| day_info | Day 1A |

---

## 4. 버전 타입 분류

### 4.1 버전 타입 목록

| 타입 | 파일명 특징 | 설명 |
|------|------------|------|
| `clean` | `-clean`, `클린본` | 원본 클린 버전 |
| `mastered` | Mastered 폴더 | 마스터링 완료 |
| `stream` | STREAM 폴더 | 풀 스트림 녹화 |
| `subclip` | SUBCLIP 폴더 | 하이라이트 클립 |
| `final_edit` | `final_edit` | 최종 편집본 |
| `nobug` | `-nobug` | 버그 없는 버전 |
| `pgm` | `pgm` | 프로그램 출력 |
| `hires` | `HiRes` | 고해상도 |
| `generic` | 해당 없음 | 기본 버전 |

### 4.2 분류 로직

```python
def detect_version_type(file_path: str, file_name: str) -> str:
    name_lower = file_name.lower()
    path_lower = file_path.lower()

    if "-clean" in name_lower or "클린본" in file_name:
        return "clean"
    if "/mastered/" in path_lower:
        return "mastered"
    if "/stream/" in path_lower:
        return "stream"
    if "/subclip/" in path_lower:
        return "subclip"
    if "final_edit" in name_lower:
        return "final_edit"
    if "-nobug" in name_lower:
        return "nobug"
    if "pgm" in name_lower:
        return "pgm"
    if "hires" in name_lower:
        return "hires"
    return "generic"
```

---

## 5. 숨김 파일 처리

### 5.1 숨김 기준

| 파일 유형 | 패턴 | 처리 |
|----------|------|------|
| macOS 메타데이터 | `._*` | `is_hidden=True` |
| Windows 썸네일 | `Thumbs.db` | `is_hidden=True` |
| 시스템 파일 | `.DS_Store` | `is_hidden=True` |

### 5.2 숨김 처리 코드

```python
def should_hide_file(file_name: str) -> tuple[bool, str | None]:
    if file_name.startswith("._"):
        return True, "macos_metadata"
    if file_name.lower() == "thumbs.db":
        return True, "windows_thumbnail"
    if file_name == ".DS_Store":
        return True, "macos_system"
    return False, None
```

---

## 6. API

### 6.1 에이전트 인터페이스

```python
class NASInventoryAgent(BaseAgent):
    block_id = "A"

    async def scan_nas(self, base_path: str = NAS_BASE_PATH) -> ScanResult:
        """NAS 전체 스캔"""
        pass

    async def scan_folder(self, folder_path: str) -> list[NASFile]:
        """단일 폴더 스캔"""
        pass

    def parse_filename(self, file_name: str, file_path: str) -> ParsedMetadata:
        """파일명 파싱"""
        pass

    def detect_version(self, file_path: str, file_name: str) -> str:
        """버전 타입 감지"""
        pass

    async def get_file_metadata(self, file_path: str) -> FileMetadata:
        """파일 메타데이터 (크기, 수정일 등)"""
        pass

    async def detect_changes(self, since: datetime) -> list[FileChange]:
        """변경 감지 (증분 스캔)"""
        pass
```

### 6.2 이벤트 발행

```python
# 스캔 완료 시
await self.emit(EventType.NAS_SCAN_COMPLETED, {
    "total_files": 1373,
    "total_folders": 114,
    "total_size_bytes": 21474836480000,  # ~19.5TB
    "new_files": 5,
    "removed_files": 0,
    "duration_seconds": 180,
})

# 파일 추가 시
await self.emit(EventType.NAS_FILE_ADDED, {
    "file_path": "\\\\10.10.100.122\\...\\new_video.mp4",
    "file_name": "new_video.mp4",
    "parsed_metadata": {...},
})
```

---

## 7. 데이터 모델

### 7.1 NASFolder

```python
class NASFolder(Base, TimestampMixin):
    __tablename__ = "nas_folders"

    id: Mapped[UUID]
    folder_path: Mapped[str]        # unique
    folder_name: Mapped[str]
    parent_path: Mapped[str | None]
    depth: Mapped[int]              # 0부터 시작
    file_count: Mapped[int]
    folder_count: Mapped[int]
    total_size_bytes: Mapped[int]
    is_empty: Mapped[bool]
    is_hidden_folder: Mapped[bool]
```

### 7.2 NASFile

```python
class NASFile(Base, TimestampMixin):
    __tablename__ = "nas_files"

    id: Mapped[UUID]
    file_path: Mapped[str]          # unique
    file_name: Mapped[str]
    file_size_bytes: Mapped[int]
    file_extension: Mapped[str | None]
    file_mtime: Mapped[datetime | None]
    file_category: Mapped[str]      # video, metadata, system, archive, other
    is_hidden_file: Mapped[bool]
    folder_id: Mapped[UUID | None]  # FK → NASFolder
    video_file_id: Mapped[UUID | None]  # FK → VideoFile
```

### 7.3 VideoFile (연결)

```python
class VideoFile(Base, TimestampMixin):
    __tablename__ = "video_files"

    # ... 기존 컬럼 ...
    nas_file: Mapped["NASFile" | None] = relationship(back_populates="video_file")
```

---

## 8. 성능 요구사항

| 지표 | 목표 |
|------|------|
| 전체 스캔 시간 | < 300초 (1,400 파일) |
| 단일 파일 파싱 | < 10ms |
| 메모리 사용량 | < 256MB |
| 파일 경로 정확성 | 100% (Windows 탐색기 일치) |
| 파싱 정확성 | > 95% |

---

## 9. 테스트 케이스

### 9.1 파서 테스트

```python
@pytest.mark.parametrize("filename,expected", [
    (
        "10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten.mp4",
        {"year": 2024, "event_number": 21, "buy_in": "25k", "game_type": "nlh"}
    ),
    (
        "E01_GOG_final_edit_231106.mp4",
        {"episode_number": 1, "version_type": "final_edit", "edit_date": "2023-11-06"}
    ),
])
def test_parser_patterns(filename, expected):
    parser = ParserFactory.get_parser(f"/test/{filename}")
    result = parser.parse(filename)
    for key, value in expected.items():
        assert result[key] == value
```

### 9.2 스캔 테스트

```python
async def test_scan_nas_folder():
    agent = NASInventoryAgent()
    result = await agent.scan_folder("/test/WSOP/2024")

    assert len(result) > 0
    assert all(f.file_path.startswith("\\\\10.10.100.122") for f in result)
```

---

## 10. 의존성

### 10.1 외부 의존성

- 없음 (독립 블럭)

### 10.2 제공 데이터

| 소비자 블럭 | 제공 데이터 |
|------------|-----------|
| D (Sheets Sync) | `file_path` → VideoFile 매칭 |
| E (API) | NAS 트리 정보, 파일 목록 |

---

**문서 버전**: 1.0.0
**작성일**: 2025-12-11
