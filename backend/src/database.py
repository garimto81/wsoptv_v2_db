"""Database Configuration - 블럭 G (Database Agent)."""

import os
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 환경 변수에서 DB URL 가져오기
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://pokervod:pokervod@localhost:5432/pokervod",
)

# 동기 URL (Alembic용)
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

# 비동기 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# 세션 팩토리
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency - DB 세션 제공."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """데이터베이스 초기화 (테이블 생성)."""
    from .models import Base

    async with engine.begin() as conn:
        # pokervod 스키마 생성
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS pokervod"))
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """데이터베이스 연결 종료."""
    await engine.dispose()
