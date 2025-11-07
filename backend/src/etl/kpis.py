"""
KPI computation engine.
Calculates financial metrics and key performance indicators.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Transaction, MetricDaily
from ..core.logging import get_logger

logger = get_logger(__name__)


class KPIEngine:
    """Engine for computing financial KPIs."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        """
        Initialize KPI engine for a tenant.
        
        Args:
            session: Database session
            tenant_id: Tenant UUID
        """
        self.session = session
        self.tenant_id = tenant_id
    
    async def get_transactions_df(
        self,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        Load transactions as pandas DataFrame.
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with transactions
        """
        stmt = (
            select(Transaction)
            .where(Transaction.tenant_id == self.tenant_id)
            .where(Transaction.date >= start_date)
            .where(Transaction.date <= end_date)
            .order_by(Transaction.date)
        )
        
        result = await self.session.execute(stmt)
        transactions = result.scalars().all()
        
        # Convert to DataFrame
        data = []
        for txn in transactions:
            data.append({
                "date": txn.date,
                "amount": float(txn.amount),
                "category": txn.category,
                "description": txn.description,
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=["date", "amount", "category", "description"])
        
        df["date"] = pd.to_datetime(df["date"])
        return df
    
    async def compute_revenue(self, start_date: date, end_date: date) -> dict[date, Decimal]:
        """Compute daily revenue."""
        df = await self.get_transactions_df(start_date, end_date)
        
        if df.empty:
            return {}
        
        # Filter revenue transactions (positive amounts)
        revenue_df = df[df["category"] == "Revenue"]
        
        # Group by date and sum
        daily_revenue = (
            revenue_df.groupby(revenue_df["date"].dt.date)["amount"]
            .sum()
            .to_dict()
        )
        
        # Convert to Decimal
        return {k: Decimal(str(v)) for k, v in daily_revenue.items()}
    
    async def compute_expenses(self, start_date: date, end_date: date) -> dict[date, Decimal]:
        """Compute daily expenses."""
        df = await self.get_transactions_df(start_date, end_date)
        
        if df.empty:
            return {}
        
        # Filter expense categories (negative amounts or expense categories)
        expense_categories = ["Expense", "SaaS", "Infrastructure", "Marketing", "Payroll", "Contractor", "Office", "Travel", "Meals & Entertainment"]
        expense_df = df[df["category"].isin(expense_categories) | (df["amount"] < 0)]
        
        # Group by date and sum (absolute values)
        daily_expenses = (
            expense_df.groupby(expense_df["date"].dt.date)["amount"]
            .apply(lambda x: abs(x.sum()))
            .to_dict()
        )
        
        return {k: Decimal(str(v)) for k, v in daily_expenses.items()}
    
    async def compute_net_cash(self, start_date: date, end_date: date) -> dict[date, Decimal]:
        """Compute daily net cash flow."""
        revenue = await self.compute_revenue(start_date, end_date)
        expenses = await self.compute_expenses(start_date, end_date)
        
        # Combine dates
        all_dates = set(revenue.keys()) | set(expenses.keys())
        
        net_cash = {}
        for dt in all_dates:
            rev = revenue.get(dt, Decimal(0))
            exp = expenses.get(dt, Decimal(0))
            net_cash[dt] = rev - exp
        
        return net_cash
    
    async def compute_burn_rate(self, days: int = 30) -> Decimal:
        """
        Compute average daily burn rate.
        
        Args:
            days: Number of days to average
        
        Returns:
            Average daily burn rate
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        expenses = await self.compute_expenses(start_date, end_date)
        
        if not expenses:
            return Decimal(0)
        
        total_expenses = sum(expenses.values())
        avg_burn = total_expenses / Decimal(days)
        
        return avg_burn
    
    async def compute_runway(self, current_cash: Decimal | None = None) -> int:
        """
        Compute cash runway in days.
        
        Args:
            current_cash: Current cash balance (if None, computed from transactions)
        
        Returns:
            Number of days until cash runs out
        """
        burn_rate = await self.compute_burn_rate()
        
        if burn_rate == 0:
            return 999  # Effectively infinite
        
        # If no current cash provided, compute from transaction history
        if current_cash is None:
            # Get all transactions to date
            df = await self.get_transactions_df(
                date(2020, 1, 1),  # Far past date
                date.today(),
            )
            
            if df.empty:
                current_cash = Decimal(0)
            else:
                current_cash = Decimal(str(df["amount"].sum()))
        
        if current_cash <= 0:
            return 0
        
        runway_days = int(current_cash / burn_rate)
        return runway_days
    
    async def compute_growth_rate(self, period_days: int = 30) -> dict[str, Decimal]:
        """
        Compute revenue growth rate.
        
        Args:
            period_days: Period to compare
        
        Returns:
            Dictionary with growth metrics
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days * 2)
        
        revenue = await self.compute_revenue(start_date, end_date)
        
        if not revenue:
            return {"growth_rate": Decimal(0), "current_period": Decimal(0), "previous_period": Decimal(0)}
        
        # Split into two periods
        mid_date = end_date - timedelta(days=period_days)
        
        current_period = sum(
            v for k, v in revenue.items() if k > mid_date
        )
        previous_period = sum(
            v for k, v in revenue.items() if k <= mid_date
        )
        
        if previous_period == 0:
            growth_rate = Decimal(0)
        else:
            growth_rate = ((current_period - previous_period) / previous_period) * 100
        
        return {
            "growth_rate": growth_rate,
            "current_period": current_period,
            "previous_period": previous_period,
        }
    
    async def save_metrics(
        self,
        metric_name: str,
        values: dict[date, Decimal],
    ) -> None:
        """
        Save computed metrics to database.
        
        Args:
            metric_name: Name of the metric
            values: Dictionary mapping date to value
        """
        for dt, value in values.items():
            metric = MetricDaily(
                tenant_id=self.tenant_id,
                date=dt,
                metric=metric_name,
                value=value,
            )
            self.session.add(metric)
        
        await self.session.commit()
        logger.info(f"Saved {len(values)} {metric_name} metrics for tenant {self.tenant_id}")
    
    async def compute_all_kpis(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """
        Compute all KPIs for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            Dictionary of KPIs
        """
        # Compute metrics
        revenue = await self.compute_revenue(start_date, end_date)
        expenses = await self.compute_expenses(start_date, end_date)
        net_cash = await self.compute_net_cash(start_date, end_date)
        burn_rate = await self.compute_burn_rate()
        runway = await self.compute_runway()
        growth = await self.compute_growth_rate()
        
        # Save daily metrics
        await self.save_metrics("revenue", revenue)
        await self.save_metrics("expenses", expenses)
        await self.save_metrics("net_cash", net_cash)
        
        # Calculate totals for period
        total_revenue = sum(revenue.values())
        total_expenses = sum(expenses.values())
        total_net = sum(net_cash.values())
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "totals": {
                "revenue": float(total_revenue),
                "expenses": float(total_expenses),
                "net_cash": float(total_net),
            },
            "averages": {
                "daily_revenue": float(total_revenue / len(revenue) if revenue else 0),
                "daily_expenses": float(total_expenses / len(expenses) if expenses else 0),
                "burn_rate": float(burn_rate),
            },
            "metrics": {
                "runway_days": runway,
                "growth_rate_pct": float(growth["growth_rate"]),
            },
        }
