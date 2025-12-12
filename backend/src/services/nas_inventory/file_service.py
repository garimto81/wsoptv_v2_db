"""NASFile Service - Block A (NAS Inventory Agent).

NAS 파일 인벤토리 관리 서비스.
"""

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..catalog.base_service import BaseService
from ...models.nas_file import NASFile, FileCategory


class NASFileService(BaseService[NASFile]):
    """Service for NASFile entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, NASFile)

    # ==================== 조회 메서드 ====================

    async def get_by_path(self, file_path: str) -> Optional[NASFile]:
        """Get file by path."""
        result = await self.session.execute(
            select(NASFile).where(NASFile.file_path == file_path)
        )
        return result.scalar_one_or_none()

    async def get_by_folder(
        self,
        folder_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get all files in a folder."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.folder_id == folder_id)
            .order_by(NASFile.file_name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_category(
        self,
        category: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get files by category."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.file_category == category)
            .order_by(NASFile.file_name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_extension(
        self,
        extension: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get files by extension."""
        # Normalize extension (ensure starts with dot)
        ext = extension if extension.startswith(".") else f".{extension}"
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.file_extension == ext.lower())
            .order_by(NASFile.file_name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_folder(self, file_id: UUID) -> Optional[NASFile]:
        """Get file with folder loaded."""
        result = await self.session.execute(
            select(NASFile)
            .options(selectinload(NASFile.folder))
            .where(NASFile.id == file_id)
        )
        return result.scalar_one_or_none()

    async def get_with_video(self, file_id: UUID) -> Optional[NASFile]:
        """Get file with linked video file loaded."""
        result = await self.session.execute(
            select(NASFile)
            .options(selectinload(NASFile.video_file))
            .where(NASFile.id == file_id)
        )
        return result.scalar_one_or_none()

    # ==================== 생성/수정 메서드 ====================

    async def create_file(
        self,
        file_path: str,
        file_name: str,
        *,
        file_size_bytes: int = 0,
        folder_id: Optional[UUID] = None,
        file_extension: Optional[str] = None,
        file_mtime: Optional[datetime] = None,
        file_category: str = FileCategory.OTHER,
        is_hidden_file: bool = False,
    ) -> NASFile:
        """Create a new file entry."""
        return await self.create(
            file_path=file_path,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            folder_id=folder_id,
            file_extension=file_extension.lower() if file_extension else None,
            file_mtime=file_mtime,
            file_category=file_category,
            is_hidden_file=is_hidden_file,
        )

    async def update_metadata(
        self,
        file_id: UUID,
        *,
        file_size_bytes: Optional[int] = None,
        file_mtime: Optional[datetime] = None,
    ) -> Optional[NASFile]:
        """Update file metadata."""
        file = await self.get_by_id(file_id)
        if file is None:
            return None

        if file_size_bytes is not None:
            file.file_size_bytes = file_size_bytes
        if file_mtime is not None:
            file.file_mtime = file_mtime

        await self.session.flush()
        await self.session.refresh(file)
        return file

    async def set_category(
        self,
        file_id: UUID,
        category: str,
    ) -> Optional[NASFile]:
        """Set file category."""
        return await self.update(file_id, file_category=category)

    async def mark_hidden(
        self,
        file_id: UUID,
        is_hidden: bool = True,
    ) -> Optional[NASFile]:
        """Mark file as hidden."""
        return await self.update(file_id, is_hidden_file=is_hidden)

    async def link_to_video(
        self,
        file_id: UUID,
        video_file_id: UUID,
    ) -> Optional[NASFile]:
        """Link NAS file to a VideoFile."""
        return await self.update(file_id, video_file_id=video_file_id)

    async def unlink_video(self, file_id: UUID) -> Optional[NASFile]:
        """Unlink NAS file from VideoFile."""
        return await self.update(file_id, video_file_id=None)

    # ==================== 검색/필터 메서드 ====================

    async def get_video_files(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get all video category files."""
        return await self.get_by_category(FileCategory.VIDEO, skip=skip, limit=limit)

    async def get_hidden_files(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get all hidden files."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.is_hidden_file == True)  # noqa: E712
            .order_by(NASFile.file_path)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_unlinked_videos(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get video files not linked to a VideoFile record."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.file_category == FileCategory.VIDEO)
            .where(NASFile.video_file_id == None)  # noqa: E711
            .order_by(NASFile.file_path)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_unlinked_videos(self) -> int:
        """Count video files not linked to a VideoFile record."""
        result = await self.session.execute(
            select(func.count())
            .select_from(NASFile)
            .where(NASFile.file_category == FileCategory.VIDEO)
            .where(NASFile.video_file_id == None)  # noqa: E711
        )
        return result.scalar() or 0

    async def get_linked_videos(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get video files linked to a VideoFile record."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.file_category == FileCategory.VIDEO)
            .where(NASFile.video_file_id != None)  # noqa: E711
            .order_by(NASFile.file_path)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_linked_videos(self) -> int:
        """Count video files linked to a VideoFile record."""
        result = await self.session.execute(
            select(func.count())
            .select_from(NASFile)
            .where(NASFile.file_category == FileCategory.VIDEO)
            .where(NASFile.video_file_id != None)  # noqa: E711
        )
        return result.scalar() or 0

    async def get_large_files(
        self,
        min_size_bytes: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get files larger than specified size."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.file_size_bytes >= min_size_bytes)
            .order_by(desc(NASFile.file_size_bytes))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_largest_files(
        self,
        *,
        limit: int = 10,
    ) -> Sequence[NASFile]:
        """Get largest files by size."""
        result = await self.session.execute(
            select(NASFile)
            .order_by(desc(NASFile.file_size_bytes))
            .limit(limit)
        )
        return result.scalars().all()

    async def search_by_name(
        self,
        query: str,
        *,
        limit: int = 50,
    ) -> Sequence[NASFile]:
        """Search files by name (case-insensitive contains)."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.file_name.ilike(f"%{query}%"))
            .order_by(NASFile.file_name)
            .limit(limit)
        )
        return result.scalars().all()

    async def search_by_path(
        self,
        query: str,
        *,
        limit: int = 50,
    ) -> Sequence[NASFile]:
        """Search files by path (case-insensitive contains)."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.file_path.ilike(f"%{query}%"))
            .order_by(NASFile.file_path)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_or_create(
        self,
        file_path: str,
        file_name: str,
        *,
        file_size_bytes: int = 0,
        folder_id: Optional[UUID] = None,
        file_extension: Optional[str] = None,
        file_category: str = FileCategory.OTHER,
    ) -> tuple[NASFile, bool]:
        """Get existing file or create new one.

        Returns:
            Tuple of (file, created) where created is True if newly created.
        """
        existing = await self.get_by_path(file_path)
        if existing:
            return existing, False

        file = await self.create_file(
            file_path=file_path,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            folder_id=folder_id,
            file_extension=file_extension,
            file_category=file_category,
        )
        return file, True

    # ==================== 통계 메서드 ====================

    async def count_by_category(self) -> dict[str, int]:
        """Count files by category."""
        result = await self.session.execute(
            select(NASFile.file_category, func.count(NASFile.id))
            .group_by(NASFile.file_category)
        )
        return dict(result.all())

    async def count_by_extension(self, limit: int = 20) -> dict[str, int]:
        """Count files by extension (top N)."""
        result = await self.session.execute(
            select(NASFile.file_extension, func.count(NASFile.id))
            .where(NASFile.file_extension != None)  # noqa: E711
            .group_by(NASFile.file_extension)
            .order_by(desc(func.count(NASFile.id)))
            .limit(limit)
        )
        return dict(result.all())

    async def total_size_bytes(self) -> int:
        """Get total size of all files."""
        result = await self.session.execute(
            select(func.sum(NASFile.file_size_bytes))
        )
        return result.scalar() or 0

    async def total_size_by_category(self) -> dict[str, int]:
        """Get total size by category."""
        result = await self.session.execute(
            select(NASFile.file_category, func.sum(NASFile.file_size_bytes))
            .group_by(NASFile.file_category)
        )
        return dict(result.all())

    # ==================== 제외 파일 메서드 ====================

    async def count_excluded(self) -> int:
        """Count excluded files."""
        result = await self.session.execute(
            select(func.count())
            .select_from(NASFile)
            .where(NASFile.is_excluded == True)  # noqa: E712
        )
        return result.scalar() or 0

    async def get_excluded_files(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[NASFile]:
        """Get excluded files."""
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.is_excluded == True)  # noqa: E712
            .order_by(NASFile.file_path)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def mark_excluded(
        self,
        file_id: UUID,
        *,
        is_excluded: bool = True,
        reason: Optional[str] = None,
    ) -> Optional[NASFile]:
        """Mark file as excluded from catalog."""
        return await self.update(
            file_id,
            is_excluded=is_excluded,
            exclude_reason=reason,
        )

    async def mark_excluded_by_path_pattern(
        self,
        pattern: str,
        *,
        reason: Optional[str] = None,
    ) -> int:
        """Mark all files matching path pattern as excluded.

        Args:
            pattern: Path pattern to match (e.g., '/Clips/')
            reason: Reason for exclusion

        Returns:
            Number of files marked as excluded
        """
        # Get files matching pattern
        result = await self.session.execute(
            select(NASFile)
            .where(NASFile.file_path.ilike(f"%{pattern}%"))
            .where(NASFile.is_excluded == False)  # noqa: E712
        )
        files = result.scalars().all()

        # Mark each as excluded
        for file in files:
            file.is_excluded = True
            file.exclude_reason = reason

        await self.session.flush()
        return len(files)
