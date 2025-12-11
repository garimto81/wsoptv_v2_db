"""Google Sheets Client - Block D (Sheets Sync Agent).

Client for reading data from Google Sheets.
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


@dataclass
class SheetRange:
    """Sheet range data."""

    sheet_name: str
    start_row: int
    end_row: int
    values: list[list[Any]]

    @property
    def row_count(self) -> int:
        """Get number of rows."""
        return len(self.values)


class SheetsClient:
    """Google Sheets API client."""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    def __init__(
        self,
        credentials_path: Optional[str] = None,
    ) -> None:
        """Initialize sheets client.

        Args:
            credentials_path: Path to service account JSON file.
                             Defaults to GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        self.credentials_path = credentials_path or os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        self._service = None

    def _get_service(self):
        """Get or create Sheets service."""
        if self._service is None:
            if self.credentials_path is None:
                raise ValueError(
                    "No credentials path provided. "
                    "Set GOOGLE_APPLICATION_CREDENTIALS env var."
                )
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=self.SCOPES
            )
            self._service = build("sheets", "v4", credentials=credentials)
        return self._service

    def read_range(
        self,
        spreadsheet_id: str,
        range_name: str,
    ) -> list[list[Any]]:
        """Read a range from a spreadsheet.

        Args:
            spreadsheet_id: The spreadsheet ID.
            range_name: A1 notation range (e.g., "Sheet1!A1:Z100").

        Returns:
            List of rows, each row is a list of cell values.
        """
        service = self._get_service()
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [])

    def read_all_rows(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        *,
        start_row: int = 1,
        batch_size: int = 1000,
    ) -> SheetRange:
        """Read all rows from a sheet.

        Args:
            spreadsheet_id: The spreadsheet ID.
            sheet_name: Name of the sheet tab.
            start_row: Row to start from (1-indexed).
            batch_size: Number of rows to fetch per request.

        Returns:
            SheetRange with all data.
        """
        all_values: list[list[Any]] = []
        current_row = start_row

        while True:
            end_row = current_row + batch_size - 1
            range_name = f"'{sheet_name}'!A{current_row}:ZZ{end_row}"

            values = self.read_range(spreadsheet_id, range_name)
            if not values:
                break

            all_values.extend(values)
            current_row += len(values)

            if len(values) < batch_size:
                break

        return SheetRange(
            sheet_name=sheet_name,
            start_row=start_row,
            end_row=start_row + len(all_values) - 1,
            values=all_values,
        )

    def read_rows_from(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        start_row: int,
        limit: int = 100,
    ) -> SheetRange:
        """Read specific rows from a sheet.

        Args:
            spreadsheet_id: The spreadsheet ID.
            sheet_name: Name of the sheet tab.
            start_row: Row to start from (1-indexed).
            limit: Maximum number of rows to fetch.

        Returns:
            SheetRange with requested data.
        """
        end_row = start_row + limit - 1
        range_name = f"'{sheet_name}'!A{start_row}:ZZ{end_row}"

        values = self.read_range(spreadsheet_id, range_name)

        return SheetRange(
            sheet_name=sheet_name,
            start_row=start_row,
            end_row=start_row + len(values) - 1 if values else start_row,
            values=values,
        )

    def get_sheet_metadata(
        self,
        spreadsheet_id: str,
    ) -> dict[str, Any]:
        """Get spreadsheet metadata including sheet names.

        Args:
            spreadsheet_id: The spreadsheet ID.

        Returns:
            Spreadsheet metadata dict.
        """
        service = self._get_service()
        result = (
            service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id)
            .execute()
        )
        return {
            "title": result.get("properties", {}).get("title"),
            "sheets": [
                {
                    "id": sheet["properties"]["sheetId"],
                    "title": sheet["properties"]["title"],
                    "row_count": sheet["properties"]["gridProperties"]["rowCount"],
                    "column_count": sheet["properties"]["gridProperties"]["columnCount"],
                }
                for sheet in result.get("sheets", [])
            ],
        }

    def get_sheet_names(
        self,
        spreadsheet_id: str,
    ) -> list[str]:
        """Get list of sheet names in a spreadsheet.

        Args:
            spreadsheet_id: The spreadsheet ID.

        Returns:
            List of sheet names.
        """
        metadata = self.get_sheet_metadata(spreadsheet_id)
        return [sheet["title"] for sheet in metadata["sheets"]]
