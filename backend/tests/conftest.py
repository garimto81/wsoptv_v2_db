"""Pytest fixtures for PokerVOD tests."""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.base import Base


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


def _remove_schema_from_metadata(metadata: MetaData) -> MetaData:
    """Remove schema from all tables for SQLite compatibility."""
    for table in metadata.tables.values():
        table.schema = None
    return metadata


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async test engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Remove schema for SQLite compatibility
    _remove_schema_from_metadata(Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async test session."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session_factory() as session:
        yield session


@pytest.fixture(scope="function")
def sync_engine():
    """Create sync test engine."""
    engine = create_engine(
        TEST_SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def sync_session(sync_engine) -> Generator[Session, None, None]:
    """Create sync test session."""
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()
    yield session
    session.close()


# Test data fixtures
@pytest.fixture
def sample_project_data():
    """Sample project data for tests."""
    return {
        "code": "TEST",
        "name": "Test Project",
        "description": "Test project description",
        "nas_base_path": "/test/path",
        "filename_pattern": "TEST_*.mp4",
    }


@pytest.fixture
def sample_season_data():
    """Sample season data for tests."""
    return {
        "year": 2024,
        "name": "Test Season 2024",
        "location": "Las Vegas",
        "sub_category": "BRACELET_LV",
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for tests."""
    return {
        "name": "Test Event #1",
        "event_number": 1,
        "name_short": "TE1",
        "event_type": "bracelet",
        "game_type": "NLHE",
        "buy_in": 10000,
    }


@pytest.fixture
def sample_episode_data():
    """Sample episode data for tests."""
    return {
        "episode_number": 1,
        "day_number": 1,
        "part_number": 1,
        "title": "Test Episode",
        "episode_type": "full",
        "table_type": "final_table",
        "duration_seconds": 3600,
    }


@pytest.fixture
def sample_hand_clip_data():
    """Sample hand clip data for tests."""
    return {
        "title": "Amazing Bluff",
        "timecode": "00:15:30",
        "timecode_end": "00:16:45",
        "duration_seconds": 75,
        "hand_grade": "★★★",
        "pot_size": 500000,
        "notes": "Great hand!",
    }


@pytest.fixture
def sample_tag_data():
    """Sample tag data for tests."""
    return {
        "category": "poker_play",
        "name": "bluff",
        "name_display": "Bluff",
        "description": "Player made a bluff",
        "sort_order": 1,
    }


@pytest.fixture
def sample_player_data():
    """Sample player data for tests."""
    return {
        "name": "Phil Ivey",
        "name_display": "Phil Ivey",
        "nationality": "USA",
        "wsop_bracelets": 10,
    }
