"""SMB Scanner Service - NAS 폴더/파일 스캔.

SMB 프로토콜을 사용하여 NAS 서버의 폴더 구조와 파일을 스캔합니다.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import AsyncGenerator, Optional

from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open, FilePipePrinterAccessMask, CreateDisposition, FileAttributes, ShareAccess
from smbprotocol.file_info import FileDirectoryInformation, FileInformationClass

from ...config import NASConfig, get_settings

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """스캔 결과 데이터."""

    path: str
    name: str
    is_directory: bool
    size_bytes: int = 0
    modified_time: Optional[datetime] = None
    created_time: Optional[datetime] = None
    is_hidden: bool = False


class SMBScanner:
    """SMB Protocol Scanner for NAS.

    Usage:
        scanner = SMBScanner()
        async for item in scanner.scan_directory("/WSOP"):
            print(item.name, item.is_directory)
    """

    def __init__(self, config: Optional[NASConfig] = None) -> None:
        """Initialize scanner with config."""
        self.config = config or get_settings().nas
        self._connection: Optional[Connection] = None
        self._session: Optional[Session] = None
        self._tree: Optional[TreeConnect] = None
        self._connected = False

    @property
    def unc_path(self) -> str:
        """Get UNC path for NAS share."""
        return f"\\\\{self.config.nas_host}\\{self.config.nas_share}"

    async def connect(self) -> None:
        """Establish SMB connection to NAS."""
        if self._connected:
            return

        try:
            # Run blocking SMB connection in thread pool
            await asyncio.get_event_loop().run_in_executor(
                None, self._sync_connect
            )
            self._connected = True
            logger.info(f"Connected to NAS: {self.unc_path}")
        except Exception as e:
            logger.error(f"Failed to connect to NAS: {e}")
            raise

    def _sync_connect(self) -> None:
        """Synchronous SMB connection (runs in thread pool)."""
        # Create connection (guid instead of uuid in newer smbprotocol versions)
        self._connection = Connection(
            guid=None,
            server_name=self.config.nas_host,
            port=self.config.nas_port,
        )
        self._connection.connect(timeout=self.config.nas_timeout)

        # Create session with authentication
        self._session = Session(
            self._connection,
            username=self.config.nas_username,
            password=self.config.nas_password,
        )
        self._session.connect()

        # Connect to share
        share_path = f"\\\\{self.config.nas_host}\\{self.config.nas_share}"
        self._tree = TreeConnect(self._session, share_path)
        self._tree.connect()

    async def disconnect(self) -> None:
        """Close SMB connection."""
        if not self._connected:
            return

        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self._sync_disconnect
            )
            self._connected = False
            logger.info("Disconnected from NAS")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")

    def _sync_disconnect(self) -> None:
        """Synchronous disconnect."""
        if self._tree:
            self._tree.disconnect()
        if self._session:
            self._session.disconnect()
        if self._connection:
            self._connection.disconnect()

    async def scan_directory(
        self,
        path: str = "",
        recursive: bool = False,
        max_depth: int = 10,
    ) -> AsyncGenerator[ScanResult, None]:
        """Scan a directory and yield results.

        Args:
            path: Relative path from base (e.g., "/WSOP/2024")
            recursive: Whether to scan subdirectories
            max_depth: Maximum recursion depth

        Yields:
            ScanResult objects for each file/folder found
        """
        if not self._connected:
            await self.connect()

        # Normalize path
        full_path = self._build_path(path)

        async for result in self._scan_path(full_path, recursive, 0, max_depth):
            yield result

    def _build_path(self, relative_path: str) -> str:
        """Build full path from relative path."""
        # Remove leading slashes and combine with base path
        relative_path = relative_path.lstrip("/\\")
        if relative_path:
            return f"{self.config.nas_base_path}\\{relative_path}"
        return self.config.nas_base_path

    async def _scan_path(
        self,
        path: str,
        recursive: bool,
        current_depth: int,
        max_depth: int,
    ) -> AsyncGenerator[ScanResult, None]:
        """Internal scan implementation."""
        if current_depth > max_depth:
            return

        try:
            items = await asyncio.get_event_loop().run_in_executor(
                None, self._sync_list_directory, path
            )

            for item in items:
                yield item

                # Recurse into directories if needed
                if recursive and item.is_directory:
                    sub_path = f"{path}\\{item.name}"
                    async for sub_item in self._scan_path(
                        sub_path, recursive, current_depth + 1, max_depth
                    ):
                        yield sub_item

        except Exception as e:
            logger.error(f"Error scanning path {path}: {e}")
            raise

    def _sync_list_directory(self, path: str) -> list[ScanResult]:
        """Synchronous directory listing."""
        if not self._tree:
            raise RuntimeError("Not connected to NAS")

        results: list[ScanResult] = []

        # Open directory
        dir_open = Open(self._tree, path)
        dir_open.create(
            impersonation_level=2,  # Impersonation
            desired_access=FilePipePrinterAccessMask.FILE_READ_DATA | FilePipePrinterAccessMask.FILE_READ_ATTRIBUTES,
            file_attributes=FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
            share_access=ShareAccess.FILE_SHARE_READ,
            create_disposition=CreateDisposition.FILE_OPEN,
            create_options=0x00200021,  # DIRECTORY | SYNCHRONOUS_IO_NONALERT
        )

        try:
            # Query directory entries (newer API: pattern first, then class enum)
            query_result = dir_open.query_directory("*", FileInformationClass.FILE_DIRECTORY_INFORMATION)

            for entry in query_result:
                name = entry["file_name"].get_value().decode("utf-16-le")

                # Skip . and ..
                if name in (".", ".."):
                    continue

                # Parse attributes
                attrs = entry["file_attributes"].get_value()
                is_directory = bool(attrs & FileAttributes.FILE_ATTRIBUTE_DIRECTORY)
                is_hidden = bool(attrs & FileAttributes.FILE_ATTRIBUTE_HIDDEN)

                # Get timestamps
                created_time = self._filetime_to_datetime(
                    entry["creation_time"].get_value()
                )
                modified_time = self._filetime_to_datetime(
                    entry["last_write_time"].get_value()
                )

                # Get size
                size_bytes = entry["end_of_file"].get_value() if not is_directory else 0

                results.append(
                    ScanResult(
                        path=f"{path}\\{name}",
                        name=name,
                        is_directory=is_directory,
                        size_bytes=size_bytes,
                        modified_time=modified_time,
                        created_time=created_time,
                        is_hidden=is_hidden,
                    )
                )

        finally:
            dir_open.close()

        return results

    def _filetime_to_datetime(self, filetime) -> Optional[datetime]:
        """Convert Windows FILETIME to datetime.

        Args:
            filetime: Either an int (Windows FILETIME) or already a datetime object
        """
        # Handle if already datetime (smbprotocol may return datetime directly)
        if isinstance(filetime, datetime):
            return filetime

        # Handle None or invalid values
        if filetime is None:
            return None

        # Handle int filetime
        try:
            if not isinstance(filetime, int) or filetime <= 0:
                return None

            # FILETIME is 100-nanosecond intervals since 1601-01-01
            # Subtract difference between 1601 and 1970 (Unix epoch)
            EPOCH_DIFF = 116444736000000000
            timestamp = (filetime - EPOCH_DIFF) / 10_000_000

            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, OSError, TypeError):
            return None

    async def get_file_info(self, path: str) -> Optional[ScanResult]:
        """Get info for a specific file or directory."""
        if not self._connected:
            await self.connect()

        full_path = self._build_path(path)

        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None, self._sync_get_info, full_path
            )
            return info
        except Exception as e:
            logger.error(f"Error getting info for {path}: {e}")
            return None

    def _sync_get_info(self, path: str) -> ScanResult:
        """Get info for a specific path synchronously."""
        if not self._tree:
            raise RuntimeError("Not connected to NAS")

        # Try to open as directory first
        file_open = Open(self._tree, path)

        try:
            file_open.create(
                impersonation_level=2,
                desired_access=FilePipePrinterAccessMask.FILE_READ_ATTRIBUTES,
                file_attributes=0,
                share_access=ShareAccess.FILE_SHARE_READ,
                create_disposition=CreateDisposition.FILE_OPEN,
                create_options=0,
            )

            # Get basic info
            basic_info = file_open.query_file_information(4)  # FileBasicInformation
            standard_info = file_open.query_file_information(5)  # FileStandardInformation

            attrs = basic_info["file_attributes"].get_value()
            is_directory = bool(attrs & FileAttributes.FILE_ATTRIBUTE_DIRECTORY)
            is_hidden = bool(attrs & FileAttributes.FILE_ATTRIBUTE_HIDDEN)

            created_time = self._filetime_to_datetime(
                basic_info["creation_time"].get_value()
            )
            modified_time = self._filetime_to_datetime(
                basic_info["last_write_time"].get_value()
            )

            size_bytes = standard_info["end_of_file"].get_value() if not is_directory else 0

            return ScanResult(
                path=path,
                name=PurePosixPath(path).name,
                is_directory=is_directory,
                size_bytes=size_bytes,
                modified_time=modified_time,
                created_time=created_time,
                is_hidden=is_hidden,
            )

        finally:
            file_open.close()

    async def __aenter__(self) -> "SMBScanner":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
