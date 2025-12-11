"""NASFolder Service - Block A (NAS Inventory Agent).

NAS 폴더 구조 관리 서비스.
"""

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..catalog.base_service import BaseService
from ...models.nas_folder import NASFolder


class NASFolderService(BaseService[NASFolder]):
    """Service for NASFolder entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, NASFolder)

    # ==================== 조회 메서드 ====================

    async def get_by_path(self, folder_path: str) -> Optional[NASFolder]:
        """Get folder by path."""
        result = await self.session.execute(
            select(NASFolder).where(NASFolder.folder_path == folder_path)
        )
        return result.scalar_one_or_none()

    async def get_by_parent(
        self,
        parent_path: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFolder]:
        """Get all folders with specific parent path."""
        result = await self.session.execute(
            select(NASFolder)
            .where(NASFolder.parent_path == parent_path)
            .order_by(NASFolder.folder_name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_root_folders(self) -> Sequence[NASFolder]:
        """Get all root folders (depth=0, no parent)."""
        result = await self.session.execute(
            select(NASFolder)
            .where(NASFolder.depth == 0)
            .order_by(NASFolder.folder_name)
        )
        return result.scalars().all()

    async def get_children(self, folder_id: UUID) -> Sequence[NASFolder]:
        """Get direct children of a folder."""
        parent = await self.get_by_id(folder_id)
        if parent is None:
            return []
        return await self.get_by_parent(parent.folder_path)

    async def get_with_files(self, folder_id: UUID) -> Optional[NASFolder]:
        """Get folder with its files loaded."""
        result = await self.session.execute(
            select(NASFolder)
            .options(selectinload(NASFolder.files))
            .where(NASFolder.id == folder_id)
        )
        return result.scalar_one_or_none()

    async def get_by_depth(
        self,
        depth: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFolder]:
        """Get all folders at specific depth level."""
        result = await self.session.execute(
            select(NASFolder)
            .where(NASFolder.depth == depth)
            .order_by(NASFolder.folder_path)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_depth_range(
        self,
        min_depth: int,
        max_depth: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFolder]:
        """Get folders within depth range."""
        result = await self.session.execute(
            select(NASFolder)
            .where(NASFolder.depth >= min_depth)
            .where(NASFolder.depth <= max_depth)
            .order_by(NASFolder.depth, NASFolder.folder_path)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    # ==================== 생성/수정 메서드 ====================

    async def create_folder(
        self,
        folder_path: str,
        folder_name: str,
        *,
        parent_path: Optional[str] = None,
        depth: int = 0,
        is_hidden_folder: bool = False,
    ) -> NASFolder:
        """Create a new folder entry."""
        return await self.create(
            folder_path=folder_path,
            folder_name=folder_name,
            parent_path=parent_path,
            depth=depth,
            is_hidden_folder=is_hidden_folder,
            is_empty=True,
            file_count=0,
            folder_count=0,
            total_size_bytes=0,
        )

    async def update_stats(
        self,
        folder_id: UUID,
        *,
        file_count: int,
        folder_count: int,
        total_size_bytes: int,
    ) -> Optional[NASFolder]:
        """Update folder statistics."""
        folder = await self.get_by_id(folder_id)
        if folder is None:
            return None

        folder.file_count = file_count
        folder.folder_count = folder_count
        folder.total_size_bytes = total_size_bytes
        folder.is_empty = (file_count == 0 and folder_count == 0)

        await self.session.flush()
        await self.session.refresh(folder)
        return folder

    async def increment_file_count(
        self,
        folder_id: UUID,
        *,
        count: int = 1,
        size_bytes: int = 0,
    ) -> Optional[NASFolder]:
        """Increment file count and size."""
        folder = await self.get_by_id(folder_id)
        if folder is None:
            return None

        folder.file_count += count
        folder.total_size_bytes += size_bytes
        folder.is_empty = False

        await self.session.flush()
        await self.session.refresh(folder)
        return folder

    async def mark_hidden(
        self,
        folder_id: UUID,
        is_hidden: bool = True,
    ) -> Optional[NASFolder]:
        """Mark folder as hidden."""
        return await self.update(folder_id, is_hidden_folder=is_hidden)

    # ==================== 검색/필터 메서드 ====================

    async def get_hidden_folders(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFolder]:
        """Get all hidden folders."""
        result = await self.session.execute(
            select(NASFolder)
            .where(NASFolder.is_hidden_folder == True)  # noqa: E712
            .order_by(NASFolder.folder_path)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_empty_folders(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFolder]:
        """Get all empty folders."""
        result = await self.session.execute(
            select(NASFolder)
            .where(NASFolder.is_empty == True)  # noqa: E712
            .order_by(NASFolder.folder_path)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_largest_folders(
        self,
        *,
        limit: int = 10,
    ) -> Sequence[NASFolder]:
        """Get folders with largest total size."""
        result = await self.session.execute(
            select(NASFolder)
            .order_by(desc(NASFolder.total_size_bytes))
            .limit(limit)
        )
        return result.scalars().all()

    async def search_by_path(
        self,
        query: str,
        *,
        limit: int = 50,
    ) -> Sequence[NASFolder]:
        """Search folders by path (case-insensitive contains)."""
        result = await self.session.execute(
            select(NASFolder)
            .where(NASFolder.folder_path.ilike(f"%{query}%"))
            .order_by(NASFolder.folder_path)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_or_create(
        self,
        folder_path: str,
        folder_name: str,
        *,
        parent_path: Optional[str] = None,
        depth: int = 0,
    ) -> tuple[NASFolder, bool]:
        """Get existing folder or create new one.

        Returns:
            Tuple of (folder, created) where created is True if newly created.
        """
        existing = await self.get_by_path(folder_path)
        if existing:
            return existing, False

        folder = await self.create_folder(
            folder_path=folder_path,
            folder_name=folder_name,
            parent_path=parent_path,
            depth=depth,
        )
        return folder, True
