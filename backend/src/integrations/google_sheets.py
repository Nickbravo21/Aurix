"""
Google Sheets integration for Aurix.
Handles OAuth and data extraction from financial spreadsheets.
"""
import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httpx

from ..core.config import settings
from ..core.logging import get_logger
from ..core.security import token_encryption

logger = get_logger(__name__)


class GoogleSheetsClient:
    """Client for Google Sheets API operations."""
    
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    
    def __init__(self, access_token: str, refresh_token: str | None = None) -> None:
        """Initialize with OAuth tokens."""
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=self.SCOPES,
        )
        self.service = None
    
    def _ensure_service(self) -> None:
        """Ensure Google API service is initialized."""
        if self.service is None:
            self.service = build("sheets", "v4", credentials=self.credentials)
    
    def refresh_if_needed(self) -> tuple[str, str | None]:
        """
        Refresh access token if expired.
        
        Returns:
            Tuple of (access_token, refresh_token)
        """
        if self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
            return self.credentials.token, self.credentials.refresh_token
        return self.credentials.token, self.credentials.refresh_token
    
    async def get_spreadsheet_metadata(self, spreadsheet_id: str) -> dict[str, Any]:
        """Get spreadsheet metadata (title, sheets, etc.)."""
        self._ensure_service()
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            )
            return result
        except HttpError as e:
            logger.error(f"Failed to get spreadsheet metadata: {e}")
            raise ValueError(f"Cannot access spreadsheet: {e.reason}")
    
    async def read_range(
        self, 
        spreadsheet_id: str,
        range_name: str,
        value_render_option: str = "UNFORMATTED_VALUE"
    ) -> list[list[Any]]:
        """
        Read values from a spreadsheet range.
        
        Args:
            spreadsheet_id: Google Sheets ID
            range_name: A1 notation range (e.g., "Sheet1!A1:D100")
            value_render_option: How to render values (UNFORMATTED_VALUE|FORMATTED_VALUE)
        
        Returns:
            2D array of cell values
        """
        self._ensure_service()
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueRenderOption=value_render_option,
                ).execute()
            )
            return result.get("values", [])
        except HttpError as e:
            logger.error(f"Failed to read range {range_name}: {e}")
            raise ValueError(f"Cannot read spreadsheet range: {e.reason}")
    
    async def extract_transactions(
        self,
        spreadsheet_id: str,
        range_name: str = "Sheet1!A2:E1000",
        column_mapping: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Extract financial transactions from a spreadsheet.
        
        Expected columns: Date, Description, Amount, Category, Memo
        
        Args:
            spreadsheet_id: Google Sheets ID
            range_name: Range containing transaction data
            column_mapping: Custom column index mapping
        
        Returns:
            List of transaction dictionaries
        """
        # Default column mapping (0-indexed)
        mapping = column_mapping or {
            "date": 0,
            "description": 1,
            "amount": 2,
            "category": 3,
            "memo": 4,
        }
        
        rows = await self.read_range(spreadsheet_id, range_name)
        transactions = []
        
        for row_num, row in enumerate(rows, start=2):  # Start from row 2 (skip header)
            try:
                # Skip empty rows
                if not row or all(cell == "" for cell in row):
                    continue
                
                # Extract fields with safe indexing
                def get_cell(col_name: str) -> Any:
                    idx = mapping.get(col_name, -1)
                    if idx >= 0 and idx < len(row):
                        return row[idx]
                    return None
                
                date_value = get_cell("date")
                amount_value = get_cell("amount")
                
                # Skip if required fields are missing
                if not date_value or not amount_value:
                    continue
                
                # Parse date (handle various formats)
                if isinstance(date_value, str):
                    parsed_date = datetime.strptime(date_value, "%Y-%m-%d").date()
                elif isinstance(date_value, (int, float)):
                    # Google Sheets serial date
                    parsed_date = datetime(1899, 12, 30) + timedelta(days=int(date_value))
                    parsed_date = parsed_date.date()
                else:
                    parsed_date = date_value
                
                # Parse amount
                if isinstance(amount_value, str):
                    amount_value = amount_value.replace("$", "").replace(",", "")
                    parsed_amount = Decimal(amount_value)
                else:
                    parsed_amount = Decimal(str(amount_value))
                
                transaction = {
                    "date": parsed_date,
                    "amount": parsed_amount,
                    "description": str(get_cell("description") or ""),
                    "category": str(get_cell("category") or ""),
                    "memo": str(get_cell("memo") or ""),
                    "external_id": f"sheets_{spreadsheet_id}_{row_num}",
                    "raw": {"row": row, "row_number": row_num},
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"Failed to parse row {row_num}: {e}")
                continue
        
        logger.info(f"Extracted {len(transactions)} transactions from spreadsheet")
        return transactions


def get_oauth_url(state: str) -> str:
    """
    Generate Google OAuth authorization URL.
    
    Args:
        state: State parameter for CSRF protection
    
    Returns:
        Authorization URL
    """
    from urllib.parse import urlencode
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(GoogleSheetsClient.SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    """
    Exchange authorization code for access and refresh tokens.
    
    Args:
        code: Authorization code from OAuth callback
    
    Returns:
        Token response containing access_token, refresh_token, expires_in, etc.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()
