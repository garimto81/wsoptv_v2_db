# PRD: 블럭 G - Database Agent

> **버전**: 1.0.0 | **작성일**: 2025-12-11 | **블럭 코드**: G

---

## 1. 개요

### 1.1 목적

PostgreSQL 데이터베이스와 Alembic 마이그레이션을 관리합니다. 모든 블럭의 데이터 저장 기반을 제공합니다.

### 1.2 책임 범위

| 항목 | 포함 | 제외 |
|------|------|------|
| ORM 모델 정의 (11개) | O | |
| 마이그레이션 관리 | O | |
| 트랜잭션 처리 | O | |
| 인덱스 최적화 | O | |
| 백업/복구 | O | |
| 비즈니스 로직 | | X (각 블럭) |

---

## 2. 데이터베이스 구성

### 2.1 연결 정보

```python
# Docker 환경
DATABASE_URL = "postgresql://pokervod:password@db:5432/pokervod"

# 로컬 개발
DATABASE_URL = "postgresql://pokervod:password@localhost:5432/pokervod"
```

### 2.2 스키마

```sql
-- 전용 스키마 사용
CREATE SCHEMA IF NOT EXISTS pokervod;
SET search_path TO pokervod, public;
```

---

## 3. ORM 모델 (11개)

### 3.1 모델 목록

| # | 모델 | 테이블 | 컬럼 수 | 역할 |
|---|------|--------|---------|------|
| 1 | Project | projects | 9 | 포커 시리즈 |
| 2 | Season | seasons | 10 | 연도별 시즌 |
| 3 | Event | events | 15 | 토너먼트/이벤트 |
| 4 | Episode | episodes | 12 | 영상 단위 |
| 5 | VideoFile | video_files | 22 | 비디오 메타데이터 |
| 6 | HandClip | hand_clips | 16 | 핸드 분석 |
| 7 | Tag | tags | 8 | 태그 마스터 |
| 8 | Player | players | 9 | 플레이어 정보 |
| 9 | GoogleSheetSync | google_sheet_sync | 7 | 동기화 상태 |
| 10 | NASFolder | nas_folders | 11 | 폴더 구조 |
| 11 | NASFile | nas_files | 11 | 파일 인벤토리 |

### 3.2 Base 설정

```python
# src/models/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData, func
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

class Base(DeclarativeBase):
    """명명 규칙이 포함된 Base 클래스"""
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
    """타임스탬프 공통 컬럼"""
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)
```

### 3.3 관계 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CORE ENTITIES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Project ──1:N──▶ Season ──1:N──▶ Event ──1:N──▶ Episode                │
│                                                   │                     │
│                                                   ├──1:N──▶ VideoFile  │
│                                                   │              │      │
│                                                   └──1:N──▶ HandClip   │
│                                                               │   │    │
│                                                   ┌───────────┘   │    │
│                                                   ▼               ▼    │
│                                              NASFile    Tag ◀── Player  │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                           N:N RELATIONSHIPS                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  HandClip ◀──N:N──▶ Tag      (hand_clip_tags)                           │
│  HandClip ◀──N:N──▶ Player   (hand_clip_players)                        │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                           SYNC ENTITIES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GoogleSheetSync   ◀───── 동기화 상태 추적                               │
│  NASFolder ──1:N──▶ NASFile ◀───── NAS 인벤토리                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 마이그레이션

### 4.1 Alembic 구조

```
backend/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_indexes.py
│   │   └── ...
│   ├── env.py
│   └── script.py.mako
└── alembic.ini
```

### 4.2 마이그레이션 명령어

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "add video_files table"

# 마이그레이션 적용
alembic upgrade head

# 롤백 (1단계)
alembic downgrade -1

# 현재 버전 확인
alembic current

# 마이그레이션 이력
alembic history
```

### 4.3 마이그레이션 워크플로우

```
1. Model 수정 ──────▶ src/models/*.py
2. 마이그레이션 생성 ──▶ alembic revision --autogenerate -m "description"
3. 스크립트 검토 ────▶ alembic/versions/xxx_description.py
4. 테스트 ──────────▶ upgrade → downgrade → upgrade
5. 커밋 ───────────▶ Model 변경 + Migration 스크립트
6. 배포 ───────────▶ CI/CD: alembic upgrade head
```

### 4.4 env.py 설정

```python
# alembic/env.py
from src.models.base import Base
from src.models import (
    Project, Season, Event, Episode, VideoFile,
    HandClip, Tag, Player, GoogleSheetSync,
    NASFolder, NASFile
)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema="pokervod",
        )

        with context.begin_transaction():
            context.run_migrations()
```

---

## 5. 인덱스 전략

### 5.1 주요 인덱스

```python
# Project
Index("ix_projects_code", Project.code, unique=True)

# Season
Index("ix_seasons_project_year", Season.project_id, Season.year)

# Event
Index("ix_events_season_number", Event.season_id, Event.event_number)

# Episode
Index("ix_episodes_event_id", Episode.event_id)

# VideoFile
Index("ix_video_files_file_path", VideoFile.file_path, unique=True)
Index("ix_video_files_episode_id", VideoFile.episode_id)

# HandClip
Index("ix_hand_clips_video_file_id", HandClip.video_file_id)
Index("ix_hand_clips_sheet_source_row", HandClip.sheet_source, HandClip.sheet_row_number, unique=True)

# Tag
Index("ix_tags_category_name", Tag.category, Tag.name, unique=True)

# NASFile
Index("ix_nas_files_file_path", NASFile.file_path, unique=True)
Index("ix_nas_files_folder_id", NASFile.folder_id)
```

### 5.2 풀텍스트 검색 (선택)

```sql
-- 검색 최적화를 위한 GIN 인덱스
CREATE INDEX ix_video_files_title_gin ON pokervod.video_files
USING gin(to_tsvector('english', display_title));

CREATE INDEX ix_hand_clips_notes_gin ON pokervod.hand_clips
USING gin(to_tsvector('english', notes));
```

---

## 6. 트랜잭션 관리

### 6.1 세션 관리

```python
# src/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 6.2 트랜잭션 패턴

```python
# 단일 트랜잭션
async def create_project(self, data: ProjectCreate) -> Project:
    async with self.db.begin():
        project = Project(**data.dict())
        self.db.add(project)
        await self.db.flush()
        return project

# 복합 트랜잭션 (Savepoint)
async def create_catalog_tree(self, data: CatalogTreeCreate) -> Project:
    async with self.db.begin():
        project = Project(**data.project.dict())
        self.db.add(project)

        for season_data in data.seasons:
            async with self.db.begin_nested():  # Savepoint
                season = Season(project_id=project.id, **season_data.dict())
                self.db.add(season)

        return project
```

---

## 7. 백업 및 복구

### 7.1 백업 스크립트

```bash
#!/bin/bash
# scripts/backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pokervod_backup_${TIMESTAMP}.sql"

# 데이터베이스 덤프
pg_dump -h localhost -U pokervod -d pokervod \
    --schema=pokervod \
    --format=custom \
    --file="${BACKUP_FILE}"

# S3 업로드 (선택)
# aws s3 cp "${BACKUP_FILE}" s3://pokervod-backups/
```

### 7.2 복구 스크립트

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE=$1

# 스키마 삭제 및 재생성
psql -h localhost -U pokervod -d pokervod -c "DROP SCHEMA IF EXISTS pokervod CASCADE;"
psql -h localhost -U pokervod -d pokervod -c "CREATE SCHEMA pokervod;"

# 복구
pg_restore -h localhost -U pokervod -d pokervod \
    --schema=pokervod \
    --format=custom \
    "${BACKUP_FILE}"
```

---

## 8. API

### 8.1 에이전트 인터페이스

```python
class DatabaseAgent(BaseAgent):
    block_id = "G"

    async def run_migration(self, direction: str = "upgrade") -> MigrationResult:
        """마이그레이션 실행"""
        pass

    async def get_migration_status(self) -> MigrationStatus:
        """마이그레이션 상태 조회"""
        pass

    async def backup_database(self) -> BackupResult:
        """데이터베이스 백업"""
        pass

    async def restore_database(self, backup_file: str) -> RestoreResult:
        """데이터베이스 복구"""
        pass

    async def health_check(self) -> bool:
        """DB 연결 상태 확인"""
        pass

    async def get_table_stats(self) -> dict[str, TableStats]:
        """테이블별 통계"""
        pass
```

### 8.2 이벤트 발행

```python
# 마이그레이션 완료
await self.emit(EventType.DB_MIGRATION_COMPLETED, {
    "version": "003_add_indexes",
    "direction": "upgrade",
    "success": True,
})

# 백업 완료
await self.emit(EventType.DB_BACKUP_COMPLETED, {
    "file": "pokervod_backup_20251211.sql",
    "size_mb": 250,
})
```

---

## 9. Docker 통합

### 9.1 docker-compose.yml

```yaml
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
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pokervod"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: ./backend
    command: >
      sh -c "alembic upgrade head &&
             uvicorn src.main:app --host 0.0.0.0 --port 8000"
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

### 9.2 초기화 스크립트

```sql
-- scripts/init.sql
CREATE SCHEMA IF NOT EXISTS pokervod;
GRANT ALL PRIVILEGES ON SCHEMA pokervod TO pokervod;
```

---

## 10. 성능 요구사항

| 지표 | 목표 |
|------|------|
| 연결 풀 | 10-30 |
| 쿼리 시간 (p95) | < 100ms |
| 마이그레이션 시간 | < 60초 |
| 백업 시간 | < 5분 |
| 복구 시간 | < 10분 |

### 10.1 쿼리 최적화

```python
# 1. Eager Loading
query = select(Project).options(
    selectinload(Project.seasons).selectinload(Season.events)
)

# 2. 페이지네이션
query = query.offset((page - 1) * limit).limit(limit)

# 3. 필요한 컬럼만 선택
query = select(Project.id, Project.code, Project.name)

# 4. 인덱스 힌트
query = query.with_hint(Project, "USE INDEX (ix_projects_code)")
```

---

## 11. 테스트

### 11.1 테스트 데이터베이스

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/pokervod_test"
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### 11.2 Factory 패턴

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory

class ProjectFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Project
        sqlalchemy_session_persistence = "commit"

    code = factory.Sequence(lambda n: f"PROJECT_{n}")
    name = factory.Faker("company")
    is_active = True

class SeasonFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Season

    project = factory.SubFactory(ProjectFactory)
    year = factory.Faker("year")
    name = factory.LazyAttribute(lambda o: f"{o.year} Season")
```

---

## 12. 모니터링

### 12.1 쿼리 로깅

```python
# 개발 환경에서 쿼리 로깅
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

### 12.2 슬로우 쿼리 감지

```python
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    elapsed = time.time() - context._query_start_time
    if elapsed > 0.5:  # 500ms 이상
        logger.warning(f"Slow query ({elapsed:.2f}s): {statement[:100]}")
```

---

## 13. 의존성

### 13.1 제공 기능

- 모든 블럭의 데이터 저장
- ORM 모델 정의
- 마이그레이션 관리
- 트랜잭션 처리

### 13.2 의존하는 블럭

| 블럭 | 사용 내용 |
|------|---------|
| A (NAS) | NASFolder, NASFile, VideoFile |
| B (Catalog) | Project, Season, Event, Episode |
| C (Hand Analysis) | HandClip, Tag, Player |
| D (Sheets Sync) | GoogleSheetSync |
| E (API) | 모든 모델 조회 |

---

**문서 버전**: 1.0.0
**작성일**: 2025-12-11
