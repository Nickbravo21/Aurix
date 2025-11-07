"""
QuickBooks Online integration for Aurix.
Handles OAuth and financial data extraction.
"""
import asyncio
from datetime import datetime, date
from decimal import Decimal
from typing import Any
from uuid import UUID

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
import httpx

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class QuickBooksClient:
    """Client for QuickBooks Online API operations."""
    
    SCOPES = [
        Scopes.ACCOUNTING,
    ]
    
    BASE_URL_PRODUCTION = "https://quickbooks.api.intuit.com/v3/company"
    BASE_URL_SANDBOX = "https://sandbox-quickbooks.api.intuit.com/v3/company"
    
    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        realm_id: str,
        environment: str = "sandbox"
    ) -> None:
        """
        Initialize QuickBooks client.
        
        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            realm_id: QuickBooks company ID
            environment: 'sandbox' or 'production'
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.realm_id = realm_id
        self.environment = environment
        
        self.base_url = (
            self.BASE_URL_SANDBOX if environment == "sandbox"
            else self.BASE_URL_PRODUCTION
        )
        
        self.auth_client = AuthClient(
            client_id=settings.quickbooks_client_id,
            client_secret=settings.quickbooks_client_secret,
            redirect_uri=settings.quickbooks_redirect_uri,
            environment=environment,
        )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request."""
        url = f"{self.base_url}/{self.realm_id}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def refresh_tokens(self) -> dict[str, str]:
        """
        Refresh access token using refresh token.
        
        Returns:
            Dict with new access_token and refresh_token
        """
        loop = asyncio.get_event_loop()
        self.auth_client.refresh(refresh_token=self.refresh_token)
        
        return {
            "access_token": self.auth_client.access_token,
            "refresh_token": self.auth_client.refresh_token,
        }
    
    async def get_accounts(self) -> list[dict[str, Any]]:
        """Fetch chart of accounts."""
        query = "SELECT * FROM Account WHERE Active = true"
        result = await self._request("GET", "query", params={"query": query})
        
        accounts = result.get("QueryResponse", {}).get("Account", [])
        return accounts
    
    async def get_transactions(
        self,
        start_date: date,
        end_date: date,
        transaction_type: str = "Purchase",
    ) -> list[dict[str, Any]]:
        """
        Fetch transactions within date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            transaction_type: Type of transaction (Purchase, JournalEntry, etc.)
        
        Returns:
            List of transaction dictionaries
        """
        query = (
            f"SELECT * FROM {transaction_type} "
            f"WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}' "
            f"ORDERBY TxnDate DESC"
        )
        
        result = await self._request("GET", "query", params={"query": query})
        transactions = result.get("QueryResponse", {}).get(transaction_type, [])
        
        return transactions
    
    async def extract_transactions(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Extract normalized transactions from QuickBooks.
        
        Returns:
            List of normalized transaction dictionaries
        """
        # Fetch both purchases and expenses
        purchases = await self.get_transactions(start_date, end_date, "Purchase")
        expenses = await self.get_transactions(start_date, end_date, "JournalEntry")
        
        normalized = []
        
        # Normalize purchases
        for purchase in purchases:
            try:
                txn_date = datetime.strptime(purchase["TxnDate"], "%Y-%m-%d").date()
                total_amount = Decimal(str(purchase.get("TotalAmt", 0)))
                
                transaction = {
                    "date": txn_date,
                    "amount": total_amount,
                    "description": purchase.get("PrivateNote", ""),
                    "category": "Expense",
                    "memo": purchase.get("PaymentType", ""),
                    "external_id": f"qbo_purchase_{purchase['Id']}",
                    "raw": purchase,
                }
                
                normalized.append(transaction)
            except Exception as e:
                logger.warning(f"Failed to normalize purchase {purchase.get('Id')}: {e}")
                continue
        
        # Normalize journal entries
        for entry in expenses:
            try:
                txn_date = datetime.strptime(entry["TxnDate"], "%Y-%m-%d").date()
                
                # Process line items
                for line in entry.get("Line", []):
                    amount = Decimal(str(line.get("Amount", 0)))
                    
                    transaction = {
                        "date": txn_date,
                        "amount": amount,
                        "description": line.get("Description", ""),
                        "category": "Journal Entry",
                        "memo": entry.get("PrivateNote", ""),
                        "external_id": f"qbo_journal_{entry['Id']}_{line.get('Id', '')}",
                        "raw": {"entry": entry, "line": line},
                    }
                    
                    normalized.append(transaction)
            except Exception as e:
                logger.warning(f"Failed to normalize journal entry {entry.get('Id')}: {e}")
                continue
        
        logger.info(f"Extracted {len(normalized)} transactions from QuickBooks")
        return normalized


def get_oauth_url(state: str) -> str:
    """
    Generate QuickBooks OAuth authorization URL.
    
    Args:
        state: State parameter for CSRF protection
    
    Returns:
        Authorization URL
    """
    auth_client = AuthClient(
        client_id=settings.quickbooks_client_id,
        client_secret=settings.quickbooks_client_secret,
        redirect_uri=settings.quickbooks_redirect_uri,
        environment=settings.quickbooks_environment,
    )
    
    return auth_client.get_authorization_url(scopes=QuickBooksClient.SCOPES, state=state)


async def exchange_code_for_tokens(code: str, realm_id: str) -> dict[str, Any]:
    """
    Exchange authorization code for access tokens.
    
    Args:
        code: Authorization code from OAuth callback
        realm_id: QuickBooks company ID
    
    Returns:
        Token response with access_token, refresh_token, etc.
    """
    auth_client = AuthClient(
        client_id=settings.quickbooks_client_id,
        client_secret=settings.quickbooks_client_secret,
        redirect_uri=settings.quickbooks_redirect_uri,
        environment=settings.quickbooks_environment,
    )
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, auth_client.get_bearer_token, code, realm_id=realm_id)
    
    return {
        "access_token": auth_client.access_token,
        "refresh_token": auth_client.refresh_token,
        "expires_in": auth_client.expires_in,
        "realm_id": realm_id,
    }
