"""
Data normalization and transformation utilities.
Standardizes financial data from various sources.
"""
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from ..core.logging import get_logger

logger = get_logger(__name__)


# Standard categories mapping
CATEGORY_MAPPING = {
    # Income categories
    "revenue": "Revenue",
    "sales": "Revenue",
    "income": "Revenue",
    "payment": "Revenue",
    "subscription": "Revenue",
    
    # Expense categories
    "expense": "Expense",
    "cost": "Expense",
    "purchase": "Expense",
    "payment_sent": "Expense",
    
    # Specific expense types
    "saas": "SaaS",
    "software": "SaaS",
    "subscription_expense": "SaaS",
    "hosting": "Infrastructure",
    "server": "Infrastructure",
    "cloud": "Infrastructure",
    "marketing": "Marketing",
    "advertising": "Marketing",
    "ads": "Marketing",
    "payroll": "Payroll",
    "salary": "Payroll",
    "wages": "Payroll",
    "contractor": "Contractor",
    "freelance": "Contractor",
    "office": "Office",
    "supplies": "Office",
    "travel": "Travel",
    "meals": "Meals & Entertainment",
    "entertainment": "Meals & Entertainment",
    
    # Other
    "refund": "Refund",
    "fee": "Fee",
    "interest": "Interest",
    "tax": "Tax",
    "transfer": "Transfer",
}


def normalize_category(raw_category: str | None) -> str:
    """
    Normalize transaction category to standard taxonomy.
    
    Args:
        raw_category: Raw category string from data source
    
    Returns:
        Normalized category string
    """
    if not raw_category:
        return "Uncategorized"
    
    # Convert to lowercase for matching
    category_lower = raw_category.lower().strip()
    
    # Try exact match first
    if category_lower in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[category_lower]
    
    # Try partial match
    for key, value in CATEGORY_MAPPING.items():
        if key in category_lower:
            return value
    
    # Default to original category (titlecase)
    return raw_category.title()


def categorize_transaction(
    description: str,
    amount: Decimal,
    existing_category: str | None = None,
) -> str:
    """
    Infer transaction category from description and amount.
    
    Args:
        description: Transaction description
        amount: Transaction amount
        existing_category: Existing category if available
    
    Returns:
        Inferred category
    """
    if existing_category:
        return normalize_category(existing_category)
    
    desc_lower = description.lower()
    
    # Income indicators (positive amounts)
    if amount > 0:
        if any(word in desc_lower for word in ["payment received", "invoice", "sale", "deposit"]):
            return "Revenue"
    
    # Expense indicators (negative amounts)
    if amount < 0:
        # SaaS/Software
        if any(word in desc_lower for word in ["aws", "github", "stripe", "vercel", "heroku", "digitalocean", "software"]):
            return "SaaS"
        
        # Marketing
        if any(word in desc_lower for word in ["google ads", "facebook ads", "linkedin", "marketing", "advertising"]):
            return "Marketing"
        
        # Infrastructure
        if any(word in desc_lower for word in ["hosting", "server", "cloud", "domain"]):
            return "Infrastructure"
        
        # Office/Supplies
        if any(word in desc_lower for word in ["office", "supplies", "equipment"]):
            return "Office"
        
        # Travel
        if any(word in desc_lower for word in ["airline", "hotel", "uber", "lyft", "taxi", "flight"]):
            return "Travel"
        
        # Default expense
        return "Expense"
    
    return "Uncategorized"


def detect_duplicates(
    transactions: list[dict[str, Any]],
    key_fields: list[str] = ["date", "amount", "description"],
) -> list[dict[str, Any]]:
    """
    Detect and remove duplicate transactions.
    
    Args:
        transactions: List of transaction dictionaries
        key_fields: Fields to use for duplicate detection
    
    Returns:
        Deduplicated list of transactions
    """
    seen = set()
    unique = []
    duplicates = 0
    
    for txn in transactions:
        # Create a tuple of key field values
        key = tuple(txn.get(field) for field in key_fields)
        
        if key not in seen:
            seen.add(key)
            unique.append(txn)
        else:
            duplicates += 1
    
    if duplicates > 0:
        logger.info(f"Removed {duplicates} duplicate transactions")
    
    return unique


def validate_transaction(txn: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validate transaction data.
    
    Args:
        txn: Transaction dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = ["date", "amount", "external_id"]
    for field in required_fields:
        if field not in txn or txn[field] is None:
            return False, f"Missing required field: {field}"
    
    # Validate date
    if not isinstance(txn["date"], date):
        return False, "Date must be a date object"
    
    # Validate amount
    if not isinstance(txn["amount"], Decimal):
        return False, "Amount must be a Decimal"
    
    # Check for future dates
    if txn["date"] > date.today():
        return False, "Transaction date cannot be in the future"
    
    return True, None


def enrich_transaction(
    txn: dict[str, Any],
    tenant_id: UUID,
    data_source_id: UUID,
) -> dict[str, Any]:
    """
    Enrich transaction with additional metadata and normalization.
    
    Args:
        txn: Raw transaction dictionary
        tenant_id: Tenant UUID
        data_source_id: Data source UUID
    
    Returns:
        Enriched transaction dictionary
    """
    # Validate first
    is_valid, error = validate_transaction(txn)
    if not is_valid:
        raise ValueError(f"Invalid transaction: {error}")
    
    # Normalize category
    raw_category = txn.get("category")
    txn["category"] = categorize_transaction(
        txn.get("description", ""),
        txn["amount"],
        raw_category,
    )
    
    # Add tenant and data source
    txn["tenant_id"] = tenant_id
    txn["data_source_id"] = data_source_id
    
    # Ensure all fields exist
    txn.setdefault("description", "")
    txn.setdefault("memo", "")
    txn.setdefault("subcategory", None)
    txn.setdefault("account_id", None)
    
    return txn


def aggregate_by_period(
    transactions: list[dict[str, Any]],
    period: str = "daily",
    metric: str = "amount",
) -> dict[date, Decimal]:
    """
    Aggregate transactions by time period.
    
    Args:
        transactions: List of transactions
        period: Aggregation period (daily|weekly|monthly)
        metric: Metric to aggregate (amount by default)
    
    Returns:
        Dictionary mapping date to aggregated value
    """
    from collections import defaultdict
    from datetime import timedelta
    
    aggregated: dict[date, Decimal] = defaultdict(lambda: Decimal(0))
    
    for txn in transactions:
        txn_date = txn["date"]
        value = txn.get(metric, Decimal(0))
        
        # Determine aggregation key based on period
        if period == "daily":
            key = txn_date
        elif period == "weekly":
            # Start of week (Monday)
            key = txn_date - timedelta(days=txn_date.weekday())
        elif period == "monthly":
            # First day of month
            key = txn_date.replace(day=1)
        else:
            raise ValueError(f"Invalid period: {period}")
        
        aggregated[key] += value
    
    return dict(aggregated)
