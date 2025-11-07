"""
AI analyzers for financial data.
"""
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .prompts import (
    SYSTEM_PROMPT,
    FORECAST_ANALYSIS_PROMPT,
    EXPENSE_OPTIMIZATION_PROMPT,
    build_financial_context,
)
from .llm import generate_json_response
from ..etl.kpis import KPIEngine
from ..etl.forecasts import ForecastEngine
from ..core.logging import get_logger

logger = get_logger(__name__)


async def generate_financial_summary(
    session: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Generate AI summary of financial performance.
    
    Args:
        session: Database session
        tenant_id: Tenant UUID
        start_date: Analysis start date
        end_date: Analysis end date
    
    Returns:
        Dictionary with summary, insights, risks, actions
    """
    # Compute KPIs
    kpi_engine = KPIEngine(session, tenant_id)
    kpis = await kpi_engine.compute_all_kpis(start_date, end_date)
    
    # Build context for AI
    context = build_financial_context(
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        kpis=kpis,
    )
    
    # Generate AI analysis
    logger.info(f"Generating AI financial summary for tenant {tenant_id}")
    analysis = await generate_json_response(SYSTEM_PROMPT, context)
    
    # Add metadata
    analysis["period"] = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    analysis["kpis"] = kpis
    
    return analysis


async def generate_forecast_analysis(
    session: AsyncSession,
    tenant_id: UUID,
    metric: str,
    horizon_days: int = 90,
) -> dict[str, Any]:
    """
    Generate AI analysis of forecast.
    
    Args:
        session: Database session
        tenant_id: Tenant UUID
        metric: Metric to forecast
        horizon_days: Forecast horizon
    
    Returns:
        Forecast with AI interpretation
    """
    # Generate forecast
    forecast_engine = ForecastEngine(session, tenant_id)
    forecast = await forecast_engine.generate_forecast(metric, horizon_days)
    
    # Get historical KPIs for context
    kpi_engine = KPIEngine(session, tenant_id)
    end_date = date.today()
    start_date = end_date.replace(day=1)  # Start of month
    kpis = await kpi_engine.compute_all_kpis(start_date, end_date)
    
    # Build context
    context = {
        "metric": metric,
        "horizon_days": horizon_days,
        "historical_kpis": kpis,
        "forecast": {
            "predicted_values": list(forecast["series"].values())[:7],  # First 7 days
            "accuracy_score": forecast.get("accuracy_score"),
        },
    }
    
    # Generate AI analysis
    prompt = FORECAST_ANALYSIS_PROMPT.format(horizon_days=horizon_days)
    logger.info(f"Generating forecast analysis for {metric}")
    analysis = await generate_json_response(prompt, context)
    
    # Combine forecast and analysis
    result = {
        **forecast,
        "ai_analysis": analysis,
    }
    
    # Save forecast to database
    await forecast_engine.save_forecast(forecast)
    
    return result


async def generate_expense_analysis(
    session: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Generate AI analysis of expense patterns.
    
    Args:
        session: Database session
        tenant_id: Tenant UUID
        start_date: Analysis start date
        end_date: Analysis end date
    
    Returns:
        Expense analysis with optimization suggestions
    """
    from sqlalchemy import select, func
    from ..db.models import Transaction
    
    # Get expense breakdown by category
    stmt = (
        select(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .where(Transaction.tenant_id == tenant_id)
        .where(Transaction.date >= start_date)
        .where(Transaction.date <= end_date)
        .where(Transaction.amount < 0)  # Expenses are negative
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount))
    )
    
    result = await session.execute(stmt)
    expense_breakdown = []
    
    for row in result:
        expense_breakdown.append({
            "category": row.category,
            "total": float(abs(row.total)),
            "count": row.count,
        })
    
    # Get total revenue for context
    kpi_engine = KPIEngine(session, tenant_id)
    revenue_dict = await kpi_engine.compute_revenue(start_date, end_date)
    total_revenue = float(sum(revenue_dict.values()))
    
    # Build context
    context = {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "expenses_by_category": expense_breakdown,
        "total_revenue": total_revenue,
    }
    
    # Generate AI analysis
    logger.info(f"Generating expense analysis for tenant {tenant_id}")
    analysis = await generate_json_response(EXPENSE_OPTIMIZATION_PROMPT, context)
    
    return analysis


async def generate_alert_explanation(
    alert_name: str,
    metric: str,
    current_value: float,
    threshold: float,
    operator: str,
) -> str:
    """
    Generate plain-text explanation of why alert was triggered.
    
    Args:
        alert_name: Name of alert
        metric: Metric that triggered
        current_value: Current metric value
        threshold: Alert threshold
        operator: Comparison operator
    
    Returns:
        Plain text explanation
    """
    from .prompts import ALERT_SUMMARY_PROMPT
    from .llm import generate_text_response
    
    context = (
        f"Alert: {alert_name}\n"
        f"Metric: {metric}\n"
        f"Current Value: {current_value}\n"
        f"Threshold: {threshold}\n"
        f"Condition: {metric} {operator} {threshold}\n"
    )
    
    explanation = await generate_text_response(ALERT_SUMMARY_PROMPT, context)
    return explanation.strip()
