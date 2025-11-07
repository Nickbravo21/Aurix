"""
Forecasting engine using Prophet.
Generates time series forecasts for financial metrics.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import pandas as pd
from prophet import Prophet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import MetricDaily, Forecast
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class ForecastEngine:
    """Engine for generating financial forecasts using Prophet."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        """
        Initialize forecast engine.
        
        Args:
            session: Database session
            tenant_id: Tenant UUID
        """
        self.session = session
        self.tenant_id = tenant_id
    
    async def get_metric_history(
        self,
        metric: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        Load historical metric data.
        
        Args:
            metric: Metric name (e.g., 'revenue', 'expenses')
            start_date: Optional start date
            end_date: Optional end date
        
        Returns:
            DataFrame with columns: ds (date), y (value)
        """
        stmt = (
            select(MetricDaily)
            .where(MetricDaily.tenant_id == self.tenant_id)
            .where(MetricDaily.metric == metric)
        )
        
        if start_date:
            stmt = stmt.where(MetricDaily.date >= start_date)
        if end_date:
            stmt = stmt.where(MetricDaily.date <= end_date)
        
        stmt = stmt.order_by(MetricDaily.date)
        
        result = await self.session.execute(stmt)
        metrics = result.scalars().all()
        
        # Convert to Prophet format (ds, y)
        data = []
        for m in metrics:
            data.append({
                "ds": pd.Timestamp(m.date),
                "y": float(m.value),
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return pd.DataFrame(columns=["ds", "y"])
        
        return df
    
    def train_model(
        self,
        df: pd.DataFrame,
        **prophet_kwargs: Any,
    ) -> Prophet:
        """
        Train Prophet model on historical data.
        
        Args:
            df: DataFrame with ds (date) and y (value) columns
            prophet_kwargs: Additional Prophet parameters
        
        Returns:
            Fitted Prophet model
        """
        # Default parameters
        params = {
            "yearly_seasonality": False,
            "weekly_seasonality": True,
            "daily_seasonality": False,
            "changepoint_prior_scale": 0.05,
            "seasonality_mode": "multiplicative",
        }
        params.update(prophet_kwargs)
        
        model = Prophet(**params)
        model.fit(df)
        
        return model
    
    async def generate_forecast(
        self,
        metric: str,
        horizon_days: int = 90,
        min_data_points: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate forecast for a metric.
        
        Args:
            metric: Metric name
            horizon_days: Number of days to forecast
            min_data_points: Minimum required data points (defaults to config)
        
        Returns:
            Dictionary with forecast data
        """
        if min_data_points is None:
            min_data_points = settings.forecast_min_data_points
        
        # Load historical data
        df = await self.get_metric_history(metric)
        
        if df.empty or len(df) < min_data_points:
            raise ValueError(
                f"Insufficient data for forecasting. Need at least {min_data_points} data points, got {len(df)}"
            )
        
        # Train model
        logger.info(f"Training forecast model for {metric} with {len(df)} data points")
        model = self.train_model(df)
        
        # Make future dataframe
        future = model.make_future_dataframe(periods=horizon_days, freq="D")
        
        # Predict
        forecast = model.predict(future)
        
        # Extract forecast results (only future dates)
        future_forecast = forecast.tail(horizon_days)
        
        # Build series dictionary
        series = {}
        confidence_intervals = {}
        
        for _, row in future_forecast.iterrows():
            date_str = row["ds"].strftime("%Y-%m-%d")
            series[date_str] = float(row["yhat"])
            confidence_intervals[date_str] = {
                "lower": float(row["yhat_lower"]),
                "upper": float(row["yhat_upper"]),
            }
        
        # Compute simple accuracy score (MAPE on historical data)
        historical_forecast = forecast.head(len(df))
        actual = df["y"].values
        predicted = historical_forecast["yhat"].values
        
        # Mean Absolute Percentage Error
        mask = actual != 0
        if mask.any():
            mape = (abs((actual[mask] - predicted[mask]) / actual[mask])).mean()
            accuracy_score = max(0, 1 - mape)  # Convert to accuracy (0-1)
        else:
            accuracy_score = None
        
        logger.info(
            f"Generated {horizon_days}-day forecast for {metric}. "
            f"Accuracy: {accuracy_score:.2%}" if accuracy_score else "Accuracy: N/A"
        )
        
        return {
            "metric": metric,
            "horizon_days": horizon_days,
            "series": series,
            "confidence_intervals": confidence_intervals,
            "accuracy_score": accuracy_score,
            "model_type": "prophet",
            "model_params": {
                "data_points": len(df),
                "forecast_start": future_forecast.iloc[0]["ds"].strftime("%Y-%m-%d"),
                "forecast_end": future_forecast.iloc[-1]["ds"].strftime("%Y-%m-%d"),
            },
        }
    
    async def save_forecast(self, forecast_data: dict[str, Any]) -> UUID:
        """
        Save forecast to database.
        
        Args:
            forecast_data: Forecast data dictionary
        
        Returns:
            Forecast UUID
        """
        forecast = Forecast(
            tenant_id=self.tenant_id,
            metric=forecast_data["metric"],
            horizon_days=forecast_data["horizon_days"],
            series=forecast_data["series"],
            confidence_intervals=forecast_data["confidence_intervals"],
            model_type=forecast_data["model_type"],
            model_params=forecast_data["model_params"],
            accuracy_score=forecast_data.get("accuracy_score"),
        )
        
        self.session.add(forecast)
        await self.session.commit()
        await self.session.refresh(forecast)
        
        logger.info(f"Saved forecast {forecast.id} for {forecast.metric}")
        return forecast.id
    
    async def forecast_all_metrics(
        self,
        horizon_days: int = 90,
    ) -> dict[str, dict[str, Any]]:
        """
        Generate forecasts for all key metrics.
        
        Args:
            horizon_days: Forecast horizon in days
        
        Returns:
            Dictionary mapping metric name to forecast data
        """
        metrics = ["revenue", "expenses", "net_cash"]
        forecasts = {}
        
        for metric in metrics:
            try:
                forecast = await self.generate_forecast(metric, horizon_days)
                await self.save_forecast(forecast)
                forecasts[metric] = forecast
            except ValueError as e:
                logger.warning(f"Could not generate forecast for {metric}: {e}")
                forecasts[metric] = {"error": str(e)}
        
        return forecasts
    
    async def get_latest_forecast(self, metric: str) -> dict[str, Any] | None:
        """
        Get the most recent forecast for a metric.
        
        Args:
            metric: Metric name
        
        Returns:
            Forecast data or None if not found
        """
        stmt = (
            select(Forecast)
            .where(Forecast.tenant_id == self.tenant_id)
            .where(Forecast.metric == metric)
            .order_by(Forecast.created_at.desc())
            .limit(1)
        )
        
        result = await self.session.execute(stmt)
        forecast = result.scalar_one_or_none()
        
        if not forecast:
            return None
        
        return {
            "id": forecast.id,
            "metric": forecast.metric,
            "horizon_days": forecast.horizon_days,
            "series": forecast.series,
            "confidence_intervals": forecast.confidence_intervals,
            "accuracy_score": forecast.accuracy_score,
            "created_at": forecast.created_at,
        }
