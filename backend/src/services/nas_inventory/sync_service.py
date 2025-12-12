"""NAS Sync Service - NAS 스캔 결과를 DB와 동기화.

SMB Scanner를 사용하여 NAS를 스캔하고 결과를 DB에 저장합니다.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .smb_scanner import SMBScanner, ScanResult
from .folder_service import NASFolderService
from .file_service import NASFileService
from ...models.nas_file import FileCategory
from ...models.project import ProjectCode

logger = logging.getLogger(__name__)


# Video file extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}

# Metadata extensions
METADATA_EXTENSIONS = {".json", ".xml", ".srt", ".vtt", ".nfo", ".txt"}

# Archive extensions
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz"}


@dataclass
class SyncStats:
    """동기화 통계."""

    folders_created: int = 0
    folders_updated: int = 0
    files_created: int = 0
    files_updated: int = 0
    files_skipped: int = 0
    errors: int = 0
    total_size_bytes: int = 0
    duration_seconds: float = 0.0


class NASSyncService:
    """NAS Synchronization Service.

    Usage:
        async with NASSyncService(session) as sync:
            stats = await sync.sync_project("WSOP")
            print(f"Created {stats.folders_created} folders")
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize sync service."""
        self.session = session
        self.folder_service = NASFolderService(session)
        self.file_service = NASFileService(session)
        self.scanner: Optional[SMBScanner] = None

    async def __aenter__(self) -> "NASSyncService":
        """Start scanner connection."""
        self.scanner = SMBScanner()
        await self.scanner.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close scanner connection."""
        if self.scanner:
            await self.scanner.disconnect()

    async def sync_all(self, max_depth: int = 5) -> SyncStats:
        """Sync entire NAS base path."""
        if not self.scanner:
            raise RuntimeError("Scanner not initialized. Use as context manager.")

        logger.info("Starting full NAS sync...")
        start_time = datetime.now()
        stats = SyncStats()

        try:
            async for result in self.scanner.scan_directory(
                path="",
                recursive=True,
                max_depth=max_depth,
            ):
                await self._process_scan_result(result, stats)

            await self.session.commit()

        except Exception as e:
            logger.error(f"Sync error: {e}")
            stats.errors += 1
            await self.session.rollback()
            raise

        stats.duration_seconds = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"NAS sync complete: {stats.folders_created} folders, "
            f"{stats.files_created} files in {stats.duration_seconds:.1f}s"
        )
        return stats

    async def sync_project(self, project_code: str, max_depth: int = 5) -> SyncStats:
        """Sync a specific project folder.

        Args:
            project_code: Project code (e.g., "WSOP", "HCL")
            max_depth: Maximum recursion depth

        Returns:
            SyncStats with results
        """
        if not self.scanner:
            raise RuntimeError("Scanner not initialized. Use as context manager.")

        # Get NAS path for project
        nas_path = self._get_project_nas_path(project_code)
        if not nas_path:
            logger.warning(f"No NAS path for project: {project_code}")
            return SyncStats()

        logger.info(f"Syncing project {project_code} from {nas_path}...")
        start_time = datetime.now()
        stats = SyncStats()

        try:
            async for result in self.scanner.scan_directory(
                path=nas_path,
                recursive=True,
                max_depth=max_depth,
            ):
                await self._process_scan_result(result, stats)

            await self.session.commit()

        except Exception as e:
            logger.error(f"Sync error for {project_code}: {e}")
            stats.errors += 1
            await self.session.rollback()
            raise

        stats.duration_seconds = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Project {project_code} sync complete: "
            f"{stats.folders_created} folders, {stats.files_created} files"
        )
        return stats

    def _get_project_nas_path(self, project_code: str) -> Optional[str]:
        """Get NAS path for project code."""
        # Map project codes to NAS paths
        project_paths = {
            ProjectCode.WSOP: "WSOP",
            ProjectCode.HCL: "HCL",
            ProjectCode.GGMILLIONS: "GGMillions",
            ProjectCode.MPP: "MPP",
            ProjectCode.PAD: "PAD",
            ProjectCode.GOG: "GOG 최종",
        }
        return project_paths.get(project_code)

    async def _process_scan_result(self, result: ScanResult, stats: SyncStats) -> None:
        """Process a single scan result."""
        if result.is_directory:
            await self._process_folder(result, stats)
        else:
            await self._process_file(result, stats)

    async def _process_folder(self, result: ScanResult, stats: SyncStats) -> None:
        """Process folder scan result."""
        # Normalize path for storage
        folder_path = self._normalize_path(result.path)
        parent_path = self._get_parent_path(folder_path)
        depth = folder_path.count("/")

        folder, created = await self.folder_service.get_or_create(
            folder_path=folder_path,
            folder_name=result.name,
            parent_path=parent_path,
            depth=depth,
        )

        if created:
            stats.folders_created += 1
            logger.debug(f"Created folder: {folder_path}")
        else:
            stats.folders_updated += 1

        # Update hidden flag if needed
        if folder.is_hidden_folder != result.is_hidden:
            await self.folder_service.mark_hidden(folder.id, result.is_hidden)

    async def _process_file(self, result: ScanResult, stats: SyncStats) -> None:
        """Process file scan result."""
        # Skip hidden system files (macOS/Windows metadata)
        # .DS_Store, ._* (macOS resource forks), Thumbs.db (Windows thumbnails)
        if result.is_hidden and (
            result.name.startswith(".") or
            result.name.lower() == "thumbs.db"
        ):
            stats.files_skipped += 1
            return

        file_path = self._normalize_path(result.path)
        folder_path = self._get_parent_path(file_path)

        # Get file extension and category
        extension = PurePosixPath(result.name).suffix.lower()
        category = self._categorize_file(extension)

        # Get folder ID if exists
        folder = await self.folder_service.get_by_path(folder_path)
        folder_id = folder.id if folder else None

        # Create or update file
        file, created = await self.file_service.get_or_create(
            file_path=file_path,
            file_name=result.name,
            file_size_bytes=result.size_bytes,
            file_extension=extension,
            file_category=category,
            folder_id=folder_id,
        )

        # Update additional fields if just created
        if created and (result.modified_time or result.is_hidden):
            await self.file_service.update(
                file.id,
                file_mtime=result.modified_time,
                is_hidden_file=result.is_hidden,
            )

        if created:
            stats.files_created += 1
            stats.total_size_bytes += result.size_bytes
            logger.debug(f"Created file: {result.name}")
        else:
            # Update if changed (safe comparison for datetime)
            size_changed = file.file_size_bytes != result.size_bytes
            mtime_changed = (
                (file.file_mtime is None and result.modified_time is not None) or
                (file.file_mtime is not None and result.modified_time is None) or
                (file.file_mtime is not None and result.modified_time is not None and
                 file.file_mtime != result.modified_time)
            )
            if size_changed or mtime_changed:
                await self.file_service.update(
                    file.id,
                    file_size_bytes=result.size_bytes,
                    file_mtime=result.modified_time,
                )
                stats.files_updated += 1
            else:
                stats.files_skipped += 1

        # Update folder file count
        if folder_id:
            await self.folder_service.increment_file_count(
                folder_id, count=1 if created else 0, size_bytes=result.size_bytes if created else 0
            )

    def _normalize_path(self, path: str) -> str:
        """Normalize Windows path to Unix style."""
        return path.replace("\\", "/")

    def _get_parent_path(self, path: str) -> Optional[str]:
        """Get parent path from file/folder path."""
        if "/" not in path:
            return None
        return path.rsplit("/", 1)[0]

    def _categorize_file(self, extension: str) -> str:
        """Categorize file by extension."""
        if extension in VIDEO_EXTENSIONS:
            return FileCategory.VIDEO
        elif extension in METADATA_EXTENSIONS:
            return FileCategory.METADATA
        elif extension in ARCHIVE_EXTENSIONS:
            return FileCategory.ARCHIVE
        elif extension.startswith("."):
            return FileCategory.SYSTEM
        return FileCategory.OTHER


async def quick_scan(session: AsyncSession, path: str = "") -> list[ScanResult]:
    """Quick scan without DB sync (for testing).

    Args:
        session: Database session (unused, for interface consistency)
        path: Path to scan

    Returns:
        List of scan results
    """
    results = []
    async with SMBScanner() as scanner:
        async for result in scanner.scan_directory(path, recursive=False):
            results.append(result)
    return results
