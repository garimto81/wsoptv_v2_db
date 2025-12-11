"""Sheets Sync Service - Block D (Sheets Sync Agent).

Service for syncing Google Sheets data to database.
"""

from datetime import datetime, timezone
from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.google_sheet_sync import GoogleSheetSync, SheetId, SyncStatus
from ..catalog.base_service import BaseService
from .sheets_client import SheetsClient, SheetRange


class SheetsSyncService(BaseService[GoogleSheetSync]):
    """Service for Google Sheets synchronization."""

    def __init__(
        self,
        session: AsyncSession,
        sheets_client: Optional[SheetsClient] = None,
    ) -> None:
        super().__init__(session, GoogleSheetSync)
        self.sheets_client = sheets_client or SheetsClient()

    async def get_by_sheet_and_entity(
        self,
        sheet_id: str,
        entity_type: str,
    ) -> Optional[GoogleSheetSync]:
        """Get sync record by sheet ID and entity type."""
        result = await self.session.execute(
            select(GoogleSheetSync).where(
                GoogleSheetSync.sheet_id == sheet_id,
                GoogleSheetSync.entity_type == entity_type,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_sync_record(
        self,
        sheet_id: str,
        entity_type: str,
    ) -> GoogleSheetSync:
        """Get or create a sync record."""
        record = await self.get_by_sheet_and_entity(sheet_id, entity_type)
        if record is None:
            record = await self.create(
                sheet_id=sheet_id,
                entity_type=entity_type,
                last_row_synced=0,
                sync_status=SyncStatus.IDLE,
            )
        return record

    async def get_all_sync_records(self) -> Sequence[GoogleSheetSync]:
        """Get all sync records."""
        result = await self.session.execute(
            select(GoogleSheetSync).order_by(
                GoogleSheetSync.sheet_id,
                GoogleSheetSync.entity_type,
            )
        )
        return result.scalars().all()

    async def update_sync_status(
        self,
        record_id: UUID,
        status: str,
        *,
        last_row: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[GoogleSheetSync]:
        """Update sync status."""
        record = await self.get_by_id(record_id)
        if record is None:
            return None

        record.sync_status = status
        if last_row is not None:
            record.last_row_synced = last_row
        if status == SyncStatus.COMPLETED:
            record.last_synced_at = datetime.now(timezone.utc)
            record.error_message = None
        elif status == SyncStatus.FAILED:
            record.error_message = error_message

        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def start_sync(
        self,
        sheet_id: str,
        entity_type: str,
    ) -> GoogleSheetSync:
        """Start a sync operation."""
        record = await self.get_or_create_sync_record(sheet_id, entity_type)
        record.sync_status = SyncStatus.SYNCING
        record.error_message = None
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def complete_sync(
        self,
        record_id: UUID,
        last_row: int,
    ) -> Optional[GoogleSheetSync]:
        """Mark sync as completed."""
        return await self.update_sync_status(
            record_id,
            SyncStatus.COMPLETED,
            last_row=last_row,
        )

    async def fail_sync(
        self,
        record_id: UUID,
        error_message: str,
    ) -> Optional[GoogleSheetSync]:
        """Mark sync as failed."""
        return await self.update_sync_status(
            record_id,
            SyncStatus.FAILED,
            error_message=error_message,
        )

    def fetch_new_rows(
        self,
        sheet_id: str,
        sheet_name: str,
        last_row_synced: int,
        limit: int = 100,
    ) -> SheetRange:
        """Fetch new rows from sheet since last sync.

        Args:
            sheet_id: Google Spreadsheet ID.
            sheet_name: Name of the sheet tab.
            last_row_synced: Last row number that was synced.
            limit: Maximum rows to fetch.

        Returns:
            SheetRange with new rows.
        """
        start_row = last_row_synced + 1
        return self.sheets_client.read_rows_from(
            spreadsheet_id=sheet_id,
            sheet_name=sheet_name,
            start_row=start_row,
            limit=limit,
        )

    def fetch_all_rows(
        self,
        sheet_id: str,
        sheet_name: str,
    ) -> SheetRange:
        """Fetch all rows from a sheet.

        Args:
            sheet_id: Google Spreadsheet ID.
            sheet_name: Name of the sheet tab.

        Returns:
            SheetRange with all rows.
        """
        return self.sheets_client.read_all_rows(
            spreadsheet_id=sheet_id,
            sheet_name=sheet_name,
        )

    def get_sheet_info(
        self,
        sheet_id: str,
    ) -> dict[str, Any]:
        """Get sheet metadata.

        Args:
            sheet_id: Google Spreadsheet ID.

        Returns:
            Sheet metadata dict.
        """
        return self.sheets_client.get_sheet_metadata(sheet_id)

    async def get_sync_summary(self) -> dict[str, Any]:
        """Get summary of all sync operations."""
        records = await self.get_all_sync_records()

        by_status = {
            SyncStatus.IDLE: 0,
            SyncStatus.SYNCING: 0,
            SyncStatus.COMPLETED: 0,
            SyncStatus.FAILED: 0,
        }
        for record in records:
            if record.sync_status in by_status:
                by_status[record.sync_status] += 1

        return {
            "total_syncs": len(records),
            "by_status": by_status,
            "records": [
                {
                    "id": str(record.id),
                    "sheet_id": record.sheet_id,
                    "entity_type": record.entity_type,
                    "last_row_synced": record.last_row_synced,
                    "last_synced_at": (
                        record.last_synced_at.isoformat()
                        if record.last_synced_at
                        else None
                    ),
                    "status": record.sync_status,
                    "error": record.error_message,
                }
                for record in records
            ],
        }
