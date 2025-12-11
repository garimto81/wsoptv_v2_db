"""Application Configuration - Environment Variables."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class NASConfig(BaseSettings):
    """NAS SMB Connection Configuration."""

    nas_host: str = "10.10.100.122"
    nas_share: str = "docker"
    nas_base_path: str = "GGPNAs"
    nas_username: str = "GGP"
    nas_password: str = "!@QW12qw"

    # Connection settings
    nas_port: int = 445
    nas_timeout: int = 30

    class Config:
        env_prefix = "NAS_"


class Settings(BaseSettings):
    """Application Settings."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://pokervod:pokervod@localhost:5432/pokervod",
    )
    db_echo: bool = False

    # NAS
    nas: NASConfig = NASConfig()

    # App
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
