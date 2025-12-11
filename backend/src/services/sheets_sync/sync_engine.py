"""Sync Engine - Block D (Sheets Sync Agent).

Engine for syncing Google Sheets data to database.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.google_sheet_sync import SyncStatus
from .data_mapper import SheetsDataMapper, SyncResult
from .sheets_client import SheetsClient
from .sync_service import SheetsSyncService


@dataclass
class EngineSyncResult:
    """Complete result of a sync engine operation."""

    sheet_id: str
    sheet_name: str
    entity_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    sync_result: Optional[SyncResult] = None
    last_row_synced: int = 0
    error_message: Optional[str] = None


class SheetsSyncEngine:
    """Engine for syncing Google Sheets data.

    Coordinates the full sync workflow:
    1. Start sync record
    2. Fetch rows from Google Sheets
    3. Map and persist data
    4. Update sync record status
    """

    # Default sheet configurations
    DEFAULT_SHEETS = {
        "METADATA_ARCHIVE": {
            "entity_type": "hand_clip",
            "mapper_method": "sync_archive_rows",
        },
        "ICONIK_METADATA": {
            "entity_type": "hand_clip",
            "mapper_method": "sync_iconik_rows",
        },
    }

    def __init__(
        self,
        session: AsyncSession,
        sheets_client: Optional[SheetsClient] = None,
    ):
        self.session = session
        self.sheets_client = sheets_client or SheetsClient()
        self.sync_service = SheetsSyncService(session, self.sheets_client)
        self.data_mapper = SheetsDataMapper(session)

    async def sync_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        entity_type: str = "hand_clip",
        *,
        batch_size: int = 100,
        full_sync: bool = False,
    ) -> EngineSyncResult:
        """Sync a single sheet.

        Args:
            spreadsheet_id: Google Spreadsheet ID.
            sheet_name: Name of the sheet tab.
            entity_type: Type of entity being synced.
            batch_size: Number of rows per batch.
            full_sync: If True, sync all rows; otherwise incremental.

        Returns:
            EngineSyncResult with full statistics.
        """
        started_at = datetime.now(timezone.utc)
        result = EngineSyncResult(
            sheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            entity_type=entity_type,
            status=SyncStatus.SYNCING,
            started_at=started_at,
        )

        try:
            # Start sync record
            sync_record = await self.sync_service.start_sync(
                spreadsheet_id, entity_type
            )
            result.last_row_synced = sync_record.last_row_synced

            # Determine start row
            start_row = 1 if full_sync else sync_record.last_row_synced + 1

            # Fetch rows
            if full_sync:
                sheet_range = self.sheets_client.read_all_rows(
                    spreadsheet_id, sheet_name
                )
            else:
                sheet_range = self.sheets_client.read_rows_from(
                    spreadsheet_id, sheet_name, start_row, batch_size
                )

            rows = sheet_range.values if sheet_range.values else []

            if not rows:
                # No new rows
                await self.sync_service.complete_sync(
                    sync_record.id, sync_record.last_row_synced
                )
                result.status = SyncStatus.COMPLETED
                result.completed_at = datetime.now(timezone.utc)
                result.sync_result = SyncResult(total_rows=0)
                return result

            # Map and save rows
            if sheet_name.upper() in ("METADATA_ARCHIVE", "ARCHIVE"):
                sync_result = await self.data_mapper.sync_archive_rows(
                    rows, start_row
                )
            else:
                sync_result = await self.data_mapper.sync_iconik_rows(
                    rows, start_row
                )

            result.sync_result = sync_result

            # Calculate last row synced
            last_row = start_row + len(rows) - 1

            # Update sync record
            if sync_result.errors > 0 and sync_result.errors == len(rows):
                # All rows failed
                await self.sync_service.fail_sync(
                    sync_record.id,
                    "; ".join(sync_result.error_messages[:5]),  # First 5 errors
                )
                result.status = SyncStatus.FAILED
                result.error_message = f"All {len(rows)} rows failed"
            else:
                # At least some rows succeeded
                await self.sync_service.complete_sync(sync_record.id, last_row)
                result.status = SyncStatus.COMPLETED
                result.last_row_synced = last_row

            result.completed_at = datetime.now(timezone.utc)

            # Commit transaction
            await self.session.commit()

        except Exception as e:
            result.status = SyncStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now(timezone.utc)

            # Try to update sync record with error
            try:
                sync_record = await self.sync_service.get_by_sheet_and_entity(
                    spreadsheet_id, entity_type
                )
                if sync_record:
                    await self.sync_service.fail_sync(sync_record.id, str(e))
                    await self.session.commit()
            except Exception:
                pass

            # Rollback main transaction
            await self.session.rollback()

        finally:
            # Clear caches
            self.data_mapper.clear_cache()

        return result

    async def sync_all_sheets(
        self,
        spreadsheet_id: str,
        *,
        batch_size: int = 100,
        full_sync: bool = False,
    ) -> list[EngineSyncResult]:
        """Sync all configured sheets.

        Args:
            spreadsheet_id: Google Spreadsheet ID.
            batch_size: Number of rows per batch.
            full_sync: If True, sync all rows; otherwise incremental.

        Returns:
            List of EngineSyncResult for each sheet.
        """
        results = []

        # Get available sheets
        try:
            sheet_names = self.sheets_client.get_sheet_names(spreadsheet_id)
        except Exception:
            sheet_names = list(self.DEFAULT_SHEETS.keys())

        for sheet_name in sheet_names:
            if sheet_name.upper() in ("METADATA_ARCHIVE", "ARCHIVE", "ICONIK_METADATA"):
                config = self.DEFAULT_SHEETS.get(
                    sheet_name.upper(),
                    self.DEFAULT_SHEETS.get("METADATA_ARCHIVE"),
                )
                result = await self.sync_sheet(
                    spreadsheet_id,
                    sheet_name,
                    config["entity_type"],
                    batch_size=batch_size,
                    full_sync=full_sync,
                )
                results.append(result)

        return results

    async def get_sync_status(
        self,
        spreadsheet_id: str,
        entity_type: str = "hand_clip",
    ) -> dict[str, Any]:
        """Get current sync status for a sheet.

        Args:
            spreadsheet_id: Google Spreadsheet ID.
            entity_type: Type of entity.

        Returns:
            Dict with status information.
        """
        record = await self.sync_service.get_by_sheet_and_entity(
            spreadsheet_id, entity_type
        )

        if record is None:
            return {
                "sheet_id": spreadsheet_id,
                "entity_type": entity_type,
                "status": "not_started",
                "last_row_synced": 0,
                "last_synced_at": None,
            }

        return {
            "sheet_id": spreadsheet_id,
            "entity_type": entity_type,
            "status": record.sync_status,
            "last_row_synced": record.last_row_synced,
            "last_synced_at": (
                record.last_synced_at.isoformat() if record.last_synced_at else None
            ),
            "error_message": record.error_message,
        }

    async def reset_sync(
        self,
        spreadsheet_id: str,
        entity_type: str = "hand_clip",
    ) -> bool:
        """Reset sync status to start fresh.

        Args:
            spreadsheet_id: Google Spreadsheet ID.
            entity_type: Type of entity.

        Returns:
            True if reset successful.
        """
        record = await self.sync_service.get_by_sheet_and_entity(
            spreadsheet_id, entity_type
        )

        if record is None:
            return False

        record.last_row_synced = 0
        record.sync_status = SyncStatus.IDLE
        record.error_message = None
        record.last_synced_at = None

        await self.session.flush()
        await self.session.commit()
        return True
