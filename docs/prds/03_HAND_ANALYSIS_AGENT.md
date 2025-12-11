# PRD: 블럭 C - Hand Analysis Agent

> **버전**: 1.0.0 | **작성일**: 2025-12-11 | **블럭 코드**: C

---

## 1. 개요

### 1.1 목적

포커 핸드 단위 분석 데이터(타임코드, 태그, 플레이어)를 관리합니다.

### 1.2 책임 범위

| 항목 | 포함 | 제외 |
|------|------|------|
| 핸드 클립 생성/관리 | O | |
| 태그 시스템 (5 카테고리) | O | |
| 플레이어 정보 관리 | O | |
| 타임코드 처리 | O | |
| Google Sheets 동기화 | | X (블럭 D) |

---

## 2. 핸드 클립 구조

### 2.1 핸드 클립 정보

```
HandClip
├── 기본 정보
│   ├── title: 클립 제목
│   ├── timecode: 시작 시간 (H:MM:SS)
│   ├── timecode_end: 종료 시간
│   └── duration_seconds: 길이
│
├── 핸드 정보
│   ├── hand_grade: ★, ★★, ★★★
│   ├── winner_hand: JJ, QQ, AA 등
│   ├── hands_involved: 88 vs JJ
│   └── pot_size: 팟 크기
│
├── 관계
│   ├── episode_id: 에피소드 연결
│   ├── video_file_id: 비디오 파일 연결
│   ├── tags: N:N 태그 연결
│   └── players: N:N 플레이어 연결
│
└── 추적
    ├── sheet_source: 원본 Sheet (metadata_archive, iconik_metadata)
    └── sheet_row_number: 원본 행 번호
```

---

## 3. 태그 시스템

### 3.1 5가지 태그 카테고리

| 카테고리 | 설명 | 샘플 값 |
|----------|------|--------|
| `poker_play` | 포커 플레이 타입 | Preflop All-in, Cooler, Bluff, Hero Call, Suckout, Bad Beat |
| `emotion` | 감정/반응 | Stressed, Excitement, Relief, Pain, Laughing |
| `epic_hand` | 명장면 핸드 | Royal Flush, Straight Flush, Quads, Full House |
| `runout` | 런아웃 유형 | runner runner, 1out, dirty, river, turn |
| `adjective` | 수식어 | brutal, incredible, insane, sick |

### 3.2 태그 정규화

```python
# Sheets 원본 (쉼표 구분)
"Cooler, Bluff, Hero Call"

# 정규화 후
[
    Tag(category="poker_play", name="cooler"),
    Tag(category="poker_play", name="bluff"),
    Tag(category="poker_play", name="hero_call"),
]
```

### 3.3 태그 표준화 규칙

```python
def normalize_tag(raw_value: str, category: str) -> str:
    """태그 정규화"""
    # 1. 소문자 변환
    normalized = raw_value.lower().strip()

    # 2. 공백 → 언더스코어
    normalized = normalized.replace(" ", "_")

    # 3. 특수문자 제거
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)

    return normalized
```

---

## 4. 플레이어 관리

### 4.1 플레이어 정보

```python
class Player(Base, TimestampMixin):
    id: Mapped[UUID]
    name: Mapped[str]               # 고유 이름
    name_display: Mapped[str | None]  # 표시 이름
    nationality: Mapped[str | None]
    hendon_mob_id: Mapped[str | None]  # Hendon Mob 연동
    total_live_earnings: Mapped[Decimal | None]
    wsop_bracelets: Mapped[int] = 0
    is_active: Mapped[bool] = True

    hand_clips: Mapped[list["HandClip"]] = relationship(
        secondary="pokervod.hand_clip_players",
        back_populates="players"
    )
```

### 4.2 플레이어 매칭

```python
async def find_or_create_player(self, name: str) -> Player:
    """플레이어 찾기 또는 생성"""
    # 1. 정확한 이름 매칭
    player = await self._find_by_name(name)
    if player:
        return player

    # 2. 퍼지 매칭 (유사 이름)
    player = await self._fuzzy_match(name, threshold=0.85)
    if player:
        return player

    # 3. 새 플레이어 생성
    return await self._create_player(name)
```

---

## 5. 타임코드 처리

### 5.1 타임코드 형식

| 형식 | 예시 | 변환 |
|------|------|------|
| `H:MM:SS` | `6:58:55` | 25135초 |
| `HH:MM:SS` | `06:58:55` | 25135초 |
| `MM:SS` | `58:55` | 3535초 |
| 밀리초 | `25135000` | 25135초 |

### 5.2 타임코드 변환

```python
def parse_timecode(timecode: str) -> int:
    """타임코드 → 초 단위 변환"""
    # 밀리초인 경우
    if timecode.isdigit():
        return int(timecode) // 1000

    # H:MM:SS 또는 HH:MM:SS
    parts = timecode.split(":")
    if len(parts) == 3:
        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    elif len(parts) == 2:
        m, s = map(int, parts)
        return m * 60 + s

    raise ValueError(f"Invalid timecode format: {timecode}")
```

### 5.3 타임코드 유효성 검사

```python
def validate_timecode(timecode_in: str, timecode_out: str, video_duration: int | None) -> bool:
    """타임코드 유효성 검사"""
    start = parse_timecode(timecode_in)
    end = parse_timecode(timecode_out)

    # 1. 종료 > 시작
    if end <= start:
        return False

    # 2. 비디오 길이 초과 체크
    if video_duration and end > video_duration:
        return False

    # 3. 합리적인 클립 길이 (1초 ~ 30분)
    duration = end - start
    if duration < 1 or duration > 1800:
        return False

    return True
```

---

## 6. API

### 6.1 에이전트 인터페이스

```python
class HandAnalysisAgent(BaseAgent):
    block_id = "C"

    async def create_hand_clip(
        self,
        video_file_id: UUID | None = None,
        episode_id: UUID | None = None,
        timecode: str | None = None,
        timecode_end: str | None = None,
        hand_grade: str | None = None,
        winner_hand: str | None = None,
        hands_involved: str | None = None,
        sheet_source: str | None = None,
        sheet_row_number: int | None = None,
    ) -> HandClip:
        """핸드 클립 생성"""
        pass

    async def add_tags(
        self,
        clip_id: UUID,
        tags: list[dict],  # [{"category": "poker_play", "name": "bluff"}, ...]
    ) -> list[Tag]:
        """태그 추가"""
        pass

    async def link_players(
        self,
        clip_id: UUID,
        player_names: list[str],
    ) -> list[Player]:
        """플레이어 연결"""
        pass

    async def search_clips(
        self,
        tags: list[str] | None = None,
        players: list[str] | None = None,
        hand_grade: str | None = None,
        project_code: str | None = None,
    ) -> list[HandClip]:
        """클립 검색"""
        pass

    async def get_clip_stats(self) -> ClipStats:
        """클립 통계"""
        pass
```

### 6.2 이벤트 발행

```python
# 클립 생성
await self.emit(EventType.HAND_CLIP_CREATED, {
    "clip_id": str(clip.id),
    "video_file_id": str(clip.video_file_id),
    "timecode": clip.timecode,
})

# 태그 추가
await self.emit(EventType.HAND_CLIP_TAGGED, {
    "clip_id": str(clip.id),
    "tags_added": [{"category": "poker_play", "name": "bluff"}],
})
```

---

## 7. 데이터 모델

### 7.1 HandClip

```python
class HandClip(Base, TimestampMixin):
    __tablename__ = "hand_clips"
    __table_args__ = (
        UniqueConstraint("sheet_source", "sheet_row_number"),
        {"schema": "pokervod"}
    )

    id: Mapped[UUID]
    episode_id: Mapped[UUID | None]     # FK → Episode
    video_file_id: Mapped[UUID | None]  # FK → VideoFile

    # Sheet 추적
    sheet_source: Mapped[str | None]    # metadata_archive, iconik_metadata
    sheet_row_number: Mapped[int | None]

    # 콘텐츠
    title: Mapped[str | None]
    timecode: Mapped[str | None]        # H:MM:SS
    timecode_end: Mapped[str | None]
    duration_seconds: Mapped[int | None]
    notes: Mapped[str | None]

    # 핸드 정보
    hand_grade: Mapped[str | None]      # ★, ★★, ★★★
    pot_size: Mapped[int | None]
    winner_hand: Mapped[str | None]     # JJ, QQ, AA
    hands_involved: Mapped[str | None]  # 88 vs JJ

    # 관계
    tags: Mapped[list["Tag"]] = relationship(
        secondary="pokervod.hand_clip_tags",
        back_populates="hand_clips"
    )
    players: Mapped[list["Player"]] = relationship(
        secondary="pokervod.hand_clip_players",
        back_populates="hand_clips"
    )
```

### 7.2 Tag

```python
class Tag(Base, TimestampMixin):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("category", "name"),
        {"schema": "pokervod"}
    )

    id: Mapped[UUID]
    category: Mapped[str]           # poker_play, emotion, epic_hand, runout, adjective
    name: Mapped[str]               # 정규화된 이름
    name_display: Mapped[str | None]  # 표시 이름
    description: Mapped[str | None]
    sort_order: Mapped[int] = 0
    is_active: Mapped[bool] = True

    hand_clips: Mapped[list["HandClip"]] = relationship(
        secondary="pokervod.hand_clip_tags",
        back_populates="tags"
    )
```

### 7.3 연결 테이블

```python
# hand_clip_tags
hand_clip_tags = Table(
    "hand_clip_tags",
    Base.metadata,
    Column("hand_clip_id", UUID, ForeignKey("pokervod.hand_clips.id")),
    Column("tag_id", UUID, ForeignKey("pokervod.tags.id")),
    schema="pokervod",
)

# hand_clip_players
hand_clip_players = Table(
    "hand_clip_players",
    Base.metadata,
    Column("hand_clip_id", UUID, ForeignKey("pokervod.hand_clips.id")),
    Column("player_id", UUID, ForeignKey("pokervod.players.id")),
    schema="pokervod",
)
```

---

## 8. 검색 기능

### 8.1 다중 필터 검색

```python
async def search_clips(
    self,
    tags: list[str] | None = None,
    players: list[str] | None = None,
    hand_grade: str | None = None,
    project_code: str | None = None,
    year: int | None = None,
) -> list[HandClip]:
    query = select(HandClip)

    # 태그 필터 (AND 조건)
    if tags:
        for tag_name in tags:
            query = query.filter(
                HandClip.tags.any(Tag.name == tag_name)
            )

    # 플레이어 필터 (OR 조건)
    if players:
        query = query.filter(
            HandClip.players.any(Player.name.in_(players))
        )

    # 핸드 등급 필터
    if hand_grade:
        query = query.filter(HandClip.hand_grade == hand_grade)

    # 프로젝트 필터
    if project_code:
        query = query.join(Episode).join(Event).join(Season).join(Project)
        query = query.filter(Project.code == project_code)

    return await self.db.execute(query)
```

---

## 9. 성능 요구사항

| 지표 | 목표 |
|------|------|
| 클립 생성 | < 50ms |
| 태그 검색 | < 100ms |
| 플레이어 검색 | < 100ms |
| 다중 필터 검색 | < 200ms |

---

## 10. 테스트 케이스

### 10.1 클립 생성 테스트

```python
async def test_create_hand_clip():
    agent = HandAnalysisAgent()

    clip = await agent.create_hand_clip(
        timecode="6:58:55",
        timecode_end="7:00:47",
        hand_grade="★★★",
        winner_hand="JJ",
    )

    assert clip.duration_seconds == 112
    assert clip.hand_grade == "★★★"
```

### 10.2 태그 테스트

```python
async def test_add_tags():
    agent = HandAnalysisAgent()
    clip = await create_test_clip()

    tags = await agent.add_tags(clip.id, [
        {"category": "poker_play", "name": "cooler"},
        {"category": "emotion", "name": "excitement"},
    ])

    assert len(tags) == 2
    assert tags[0].name == "cooler"
```

---

## 11. 의존성

### 11.1 외부 의존성

| 블럭 | 제공 데이터 |
|------|-----------|
| B (Catalog) | `Episode` 참조 |

### 11.2 제공 데이터

| 소비자 블럭 | 제공 데이터 |
|------------|-----------|
| D (Sheets Sync) | 클립 생성 호출 |
| E (API) | 클립 검색, 태그 목록 |

---

**문서 버전**: 1.0.0
**작성일**: 2025-12-11
