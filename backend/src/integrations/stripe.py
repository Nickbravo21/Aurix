"""
Stripe integration for Aurix.
Handles payment data extraction and billing management.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any

import stripe

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

# Configure Stripe API key
stripe.api_key = settings.stripe_api_key


class StripeClient:
    """Client for Stripe API operations."""
    
    def __init__(self, account_id: str | None = None) -> None:
        """
        Initialize Stripe client.
        
        Args:
            account_id: Optional Stripe Connect account ID
        """
        self.account_id = account_id
        self.kwargs = {"stripe_account": account_id} if account_id else {}
    
    async def get_balance_transactions(
        self,
        start_date: date,
        end_date: date,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Fetch balance transactions (payouts, charges, refunds).
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Max transactions per page
        
        Returns:
            List of balance transactions
        """
        created_gte = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        created_lte = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        
        transactions = []
        has_more = True
        starting_after = None
        
        while has_more:
            params = {
                "created": {"gte": created_gte, "lte": created_lte},
                "limit": limit,
            }
            
            if starting_after:
                params["starting_after"] = starting_after
            
            response = stripe.BalanceTransaction.list(**params, **self.kwargs)
            
            transactions.extend(response.data)
            has_more = response.has_more
            
            if has_more and response.data:
                starting_after = response.data[-1].id
        
        logger.info(f"Fetched {len(transactions)} balance transactions from Stripe")
        return [txn.to_dict() for txn in transactions]
    
    async def get_charges(
        self,
        start_date: date,
        end_date: date,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch charges (successful payments)."""
        created_gte = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        created_lte = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        
        charges = []
        has_more = True
        starting_after = None
        
        while has_more:
            params = {
                "created": {"gte": created_gte, "lte": created_lte},
                "limit": limit,
            }
            
            if starting_after:
                params["starting_after"] = starting_after
            
            response = stripe.Charge.list(**params, **self.kwargs)
            
            charges.extend(response.data)
            has_more = response.has_more
            
            if has_more and response.data:
                starting_after = response.data[-1].id
        
        logger.info(f"Fetched {len(charges)} charges from Stripe")
        return [charge.to_dict() for charge in charges]
    
    async def extract_transactions(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Extract normalized transactions from Stripe.
        
        Returns:
            List of normalized transaction dictionaries
        """
        balance_txns = await self.get_balance_transactions(start_date, end_date)
        
        normalized = []
        
        for txn in balance_txns:
            try:
                # Convert timestamp to date
                txn_date = datetime.fromtimestamp(txn["created"]).date()
                
                # Convert amount from cents to dollars
                amount = Decimal(txn["amount"]) / 100
                
                # Determine category based on type
                txn_type = txn.get("type", "")
                category_map = {
                    "charge": "Revenue",
                    "payment": "Revenue",
                    "refund": "Refund",
                    "payout": "Payout",
                    "adjustment": "Adjustment",
                    "application_fee": "Fee",
                    "stripe_fee": "Fee",
                }
                category = category_map.get(txn_type, "Other")
                
                transaction = {
                    "date": txn_date,
                    "amount": amount,
                    "description": txn.get("description", f"Stripe {txn_type}"),
                    "category": category,
                    "memo": f"Fee: {Decimal(txn.get('fee', 0)) / 100}",
                    "external_id": f"stripe_{txn['id']}",
                    "raw": txn,
                }
                
                normalized.append(transaction)
                
            except Exception as e:
                logger.warning(f"Failed to normalize Stripe transaction {txn.get('id')}: {e}")
                continue
        
        logger.info(f"Extracted {len(normalized)} transactions from Stripe")
        return normalized
    
    # Billing management methods
    
    @staticmethod
    async def create_customer(email: str, name: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a Stripe customer."""
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {},
        )
        return customer.to_dict()
    
    @staticmethod
    async def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a Stripe Checkout session.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for subscription
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if user cancels
            metadata: Additional metadata
        
        Returns:
            Checkout session object
        """
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {},
        )
        return session.to_dict()
    
    @staticmethod
    async def get_subscription(subscription_id: str) -> dict[str, Any]:
        """Get subscription details."""
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription.to_dict()
    
    @staticmethod
    async def cancel_subscription(subscription_id: str) -> dict[str, Any]:
        """Cancel a subscription."""
        subscription = stripe.Subscription.delete(subscription_id)
        return subscription.to_dict()
    
    @staticmethod
    async def create_portal_session(
        customer_id: str,
        return_url: str,
    ) -> dict[str, Any]:
        """
        Create a billing portal session for customer self-service.
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session
        
        Returns:
            Portal session with URL
        """
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.to_dict()


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """
    Verify and construct Stripe webhook event.
    
    Args:
        payload: Raw request body
        sig_header: Stripe-Signature header
    
    Returns:
        Verified Stripe event
    
    Raises:
        ValueError: If signature verification fails
    """
    if not settings.stripe_webhook_secret:
        raise ValueError("Stripe webhook secret not configured")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        raise ValueError("Invalid webhook signature") from e
