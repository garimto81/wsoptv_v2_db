"""Alembic Environment - 블럭 G (Database Agent)."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# 모델 임포트 (메타데이터 등록)
from src.models import Base

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 타겟 메타데이터
target_metadata = Base.metadata

# 환경 변수에서 DB URL 오버라이드
database_url = os.getenv("DATABASE_URL")
if database_url:
    # asyncpg → psycopg2
    database_url = database_url.replace("+asyncpg", "")
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """오프라인 모드 마이그레이션."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema="pokervod",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드 마이그레이션."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # 스키마 생성
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS pokervod"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema="pokervod",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
