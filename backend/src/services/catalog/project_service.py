"""Project Service - Block B (Catalog Agent).

CRUD operations for Project entity.
"""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.project import Project, ProjectCode
from .base_service import BaseService


class ProjectService(BaseService[Project]):
    """Service for Project entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Project)

    async def get_by_code(self, code: str) -> Optional[Project]:
        """Get project by code."""
        result = await self.session.execute(
            select(Project).where(Project.code == code)
        )
        return result.scalar_one_or_none()

    async def get_with_seasons(self, code: str) -> Optional[Project]:
        """Get project with seasons loaded."""
        result = await self.session.execute(
            select(Project)
            .options(selectinload(Project.seasons))
            .where(Project.code == code)
        )
        return result.scalar_one_or_none()

    async def get_active_projects(self) -> Sequence[Project]:
        """Get all active projects."""
        result = await self.session.execute(
            select(Project).where(Project.is_active == True).order_by(Project.code)
        )
        return result.scalars().all()

    async def create_project(
        self,
        code: str,
        name: str,
        *,
        description: Optional[str] = None,
        nas_base_path: Optional[str] = None,
        filename_pattern: Optional[str] = None,
    ) -> Project:
        """Create a new project."""
        return await self.create(
            code=code,
            name=name,
            description=description,
            nas_base_path=nas_base_path,
            filename_pattern=filename_pattern,
        )

    async def deactivate(self, code: str) -> Optional[Project]:
        """Deactivate a project."""
        project = await self.get_by_code(code)
        if project is None:
            return None
        project.is_active = False
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def seed_default_projects(self) -> list[Project]:
        """Seed default 7 projects."""
        projects = []
        default_projects = [
            (ProjectCode.WSOP, "World Series of Poker", "WSOP 공식 대회 영상"),
            (ProjectCode.HCL, "Hustler Casino Live", "Hustler Casino Live 캐시게임"),
            (ProjectCode.GGMILLIONS, "GG Millions", "GG Millions 시리즈"),
            (ProjectCode.MPP, "Masters Poker Poker", "MPP 시리즈"),
            (ProjectCode.PAD, "Poker After Dark", "Poker After Dark 시리즈"),
            (ProjectCode.GOG, "Game of Gold", "Game of Gold 시리즈"),
            (ProjectCode.OTHER, "Other", "기타 포커 영상"),
        ]
        for code, name, description in default_projects:
            existing = await self.get_by_code(code)
            if existing is None:
                project = await self.create_project(
                    code=code, name=name, description=description
                )
                projects.append(project)
        return projects
