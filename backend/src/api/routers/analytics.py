"""
Analytics API router.
Provides endpoints for KPIs, forecasts, and AI summaries.
"""
from datetime import date, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.db.models import User, Tenant
from src.api.deps import get_current_user, get_current_tenant, check_ai_quota
from src.etl.kpis import KPIEngine
from src.etl.forecasts import ForecastEngine
from src.ai.analyzers import (
    generate_financial_summary,
    generate_forecast_analysis,
    generate_expense_analysis,
)
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# Response Models
# ============================================================================

class KPIResponse(BaseModel):
    """KPI response model."""
    period: dict[str, str]
    totals: dict[str, float]
    averages: dict[str, float]
    metrics: dict[str, float | int]


class ForecastResponse(BaseModel):
    """Forecast response model."""
    metric: str
    horizon_days: int
    series: dict[str, float]
    confidence_intervals: dict[str, dict[str, float]]
    accuracy_score: float | None
    created_at: str | None = None


class AISummaryResponse(BaseModel):
    """AI summary response model."""
    summary: str
    insights: list[str]
    risks: list[str]
    actions: list[str]
    period: dict[str, str]
    kpis: dict


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Get financial KPIs for a date range.
    
    Defaults to current month if dates not provided.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date.replace(day=1)  # First day of month
    
    kpi_engine = KPIEngine(session, tenant.id)
    kpis = await kpi_engine.compute_all_kpis(start_date, end_date)
    
    return kpis


@router.get("/forecast/{metric}", response_model=ForecastResponse)
async def get_forecast(
    metric: str,
    horizon_days: Annotated[int, Query(ge=7, le=365)] = 90,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate or retrieve forecast for a metric.
    
    Supported metrics: revenue, expenses, net_cash
    """
    if metric not in ["revenue", "expenses", "net_cash"]:
        raise HTTPException(status_code=400, detail="Invalid metric")
    
    forecast_engine = ForecastEngine(session, tenant.id)
    
    # Try to get latest forecast first
    latest = await forecast_engine.get_latest_forecast(metric)
    
    # If no recent forecast, generate new one
    if not latest:
        try:
            forecast_data = await forecast_engine.generate_forecast(metric, horizon_days)
            await forecast_engine.save_forecast(forecast_data)
            return forecast_data
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return latest


@router.post("/ai/summary", response_model=AISummaryResponse, dependencies=[Depends(check_ai_quota)])
async def generate_ai_summary(
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate AI-powered financial summary.
    
    Consumes AI quota.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        summary = await generate_financial_summary(
            session,
            tenant.id,
            start_date,
            end_date,
        )
        
        # Increment AI usage counter
        tenant.ai_calls_this_month += 1
        session.add(tenant)
        await session.commit()
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate AI summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@router.post("/ai/forecast-analysis", dependencies=[Depends(check_ai_quota)])
async def generate_ai_forecast_analysis(
    metric: str = Query(..., description="Metric to analyze"),
    horizon_days: Annotated[int, Query(ge=7, le=365)] = 90,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate AI analysis of forecast.
    
    Consumes AI quota.
    """
    if metric not in ["revenue", "expenses", "net_cash"]:
        raise HTTPException(status_code=400, detail="Invalid metric")
    
    try:
        analysis = await generate_forecast_analysis(
            session,
            tenant.id,
            metric,
            horizon_days,
        )
        
        # Increment AI usage counter
        tenant.ai_calls_this_month += 1
        session.add(tenant)
        await session.commit()
        
        return analysis
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate forecast analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analysis")


@router.post("/ai/expense-analysis", dependencies=[Depends(check_ai_quota)])
async def generate_ai_expense_analysis(
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate AI analysis of expense patterns.
    
    Consumes AI quota.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        analysis = await generate_expense_analysis(
            session,
            tenant.id,
            start_date,
            end_date,
        )
        
        # Increment AI usage counter
        tenant.ai_calls_this_month += 1
        session.add(tenant)
        await session.commit()
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to generate expense analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analysis")
