"""
AI Data Analysis Agents
Each agent specializes in a specific data analysis task.
"""
import io
import json
from typing import Any, Optional
from uuid import UUID

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet

from ..core.config import settings
from ..core.logging import get_logger
from ..core.ai import get_openai_client

logger = get_logger(__name__)


class DataCleanerAgent:
    """Automatically cleans and prepares data for analysis."""
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        Clean dataframe: handle NaN, detect types, normalize.
        
        Returns:
            Tuple of (cleaned_df, cleaning_report)
        """
        report = {
            "original_shape": df.shape,
            "missing_values": {},
            "duplicates_removed": 0,
            "columns_dropped": [],
            "transformations": [],
        }
        
        # Handle missing values
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                report["missing_values"][col] = int(missing_count)
                
                # Fill numeric with median, categorical with mode
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col].fillna(df[col].median(), inplace=True)
                    report["transformations"].append(f"Filled {col} with median")
                else:
                    df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "Unknown", inplace=True)
                    report["transformations"].append(f"Filled {col} with mode")
        
        # Remove duplicates
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            df = df.drop_duplicates()
            report["duplicates_removed"] = int(duplicates)
        
        # Drop columns with too many missing values (>50%)
        threshold = len(df) * 0.5
        cols_to_drop = [col for col in df.columns if df[col].isna().sum() > threshold]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            report["columns_dropped"] = cols_to_drop
        
        # Convert date columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col])
                    report["transformations"].append(f"Converted {col} to datetime")
                except:
                    pass
        
        report["final_shape"] = df.shape
        
        return df, report
    
    @staticmethod
    def detect_column_types(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """Detect and analyze column types."""
        columns_info = {}
        
        for col in df.columns:
            info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "unique_count": int(df[col].nunique()),
                "null_count": int(df[col].isna().sum()),
            }
            
            if pd.api.types.is_numeric_dtype(df[col]):
                info["type"] = "numeric"
                info["min"] = float(df[col].min())
                info["max"] = float(df[col].max())
                info["mean"] = float(df[col].mean())
                info["median"] = float(df[col].median())
                info["std"] = float(df[col].std())
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                info["type"] = "datetime"
                info["min"] = df[col].min().isoformat()
                info["max"] = df[col].max().isoformat()
            else:
                info["type"] = "categorical"
                info["top_values"] = df[col].value_counts().head(5).to_dict()
            
            columns_info[col] = info
        
        return columns_info


class StatsAgent:
    """Performs statistical analysis on datasets."""
    
    @staticmethod
    def descriptive_stats(df: pd.DataFrame) -> dict[str, Any]:
        """Generate comprehensive descriptive statistics."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        stats_dict = {
            "summary": df.describe().to_dict(),
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }
        
        # Correlation matrix for numeric columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            stats_dict["correlation"] = corr_matrix.to_dict()
            
            # Find strongest correlations
            corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_pairs.append({
                        "var1": corr_matrix.columns[i],
                        "var2": corr_matrix.columns[j],
                        "correlation": float(corr_matrix.iloc[i, j])
                    })
            
            corr_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            stats_dict["top_correlations"] = corr_pairs[:10]
        
        return stats_dict
    
    @staticmethod
    def regression_analysis(df: pd.DataFrame, target: str, features: list[str]) -> dict[str, Any]:
        """Perform linear regression analysis."""
        X = df[features].select_dtypes(include=[np.number])
        y = df[target]
        
        # Handle missing values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        model = LinearRegression()
        model.fit(X, y)
        
        predictions = model.predict(X)
        r2_score = model.score(X, y)
        
        return {
            "target": target,
            "features": features,
            "coefficients": {feat: float(coef) for feat, coef in zip(features, model.coef_)},
            "intercept": float(model.intercept_),
            "r2_score": float(r2_score),
            "feature_importance": sorted(
                [{"feature": feat, "coefficient": float(abs(coef))} 
                 for feat, coef in zip(features, model.coef_)],
                key=lambda x: x["coefficient"],
                reverse=True
            )
        }
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame) -> dict[str, Any]:
        """Detect outliers using Isolation Forest."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return {"outliers_detected": 0}
        
        X = df[numeric_cols].fillna(df[numeric_cols].median())
        
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        outliers = iso_forest.fit_predict(X)
        
        outlier_count = int((outliers == -1).sum())
        outlier_indices = df.index[outliers == -1].tolist()
        
        return {
            "outliers_detected": outlier_count,
            "outlier_percentage": float(outlier_count / len(df) * 100),
            "outlier_indices": outlier_indices[:100],  # Limit to first 100
        }


class InsightAgent:
    """Generates AI-powered insights from data analysis."""
    
    @staticmethod
    async def generate_insights(
        data_summary: dict[str, Any],
        analysis_type: str = "general"
    ) -> str:
        """Generate natural language insights using GPT-4o."""
        client = get_openai_client()
        
        prompt = f"""You are a data analyst AI. Analyze this data and provide clear, actionable insights.

Analysis Type: {analysis_type}

Data Summary:
{json.dumps(data_summary, indent=2)}

Provide:
1. Key findings (3-5 bullet points)
2. Notable patterns or trends
3. Potential concerns or opportunities
4. Actionable recommendations

Keep it concise and business-focused."""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert data analyst providing insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return "Unable to generate AI insights at this time."
    
    @staticmethod
    async def answer_question(
        df: pd.DataFrame,
        question: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Answer natural language questions about the dataset."""
        client = get_openai_client()
        
        # Get data summary for context
        summary = {
            "columns": list(df.columns),
            "shape": df.shape,
            "sample": df.head(3).to_dict(),
            "stats": df.describe().to_dict()
        }
        
        prompt = f"""You are a data analyst AI. Answer this question about the dataset:

Question: {question}

Dataset Info:
{json.dumps(summary, indent=2)}

Additional Context: {json.dumps(context) if context else 'None'}

Provide a clear, data-driven answer. If calculations are needed, explain them."""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert data analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return {
                "question": question,
                "answer": response.choices[0].message.content,
                "data_used": summary
            }
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return {
                "question": question,
                "answer": "Unable to process question at this time.",
                "error": str(e)
            }


class VizAgent:
    """Creates visualizations and charts."""
    
    @staticmethod
    def create_distribution_chart(df: pd.DataFrame, column: str) -> dict[str, Any]:
        """Create histogram/distribution chart."""
        fig = px.histogram(
            df, 
            x=column, 
            title=f"Distribution of {column}",
            template="plotly_dark"
        )
        
        return {
            "type": "histogram",
            "column": column,
            "chart_json": fig.to_json()
        }
    
    @staticmethod
    def create_correlation_heatmap(df: pd.DataFrame) -> dict[str, Any]:
        """Create correlation heatmap."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        corr = df[numeric_cols].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig.update_layout(
            title="Correlation Heatmap",
            template="plotly_dark"
        )
        
        return {
            "type": "heatmap",
            "chart_json": fig.to_json()
        }
    
    @staticmethod
    def create_time_series_chart(df: pd.DataFrame, date_col: str, value_col: str) -> dict[str, Any]:
        """Create time series line chart."""
        fig = px.line(
            df,
            x=date_col,
            y=value_col,
            title=f"{value_col} over Time",
            template="plotly_dark"
        )
        
        return {
            "type": "timeseries",
            "date_column": date_col,
            "value_column": value_col,
            "chart_json": fig.to_json()
        }
    
    @staticmethod
    def create_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, color_col: Optional[str] = None) -> dict[str, Any]:
        """Create scatter plot."""
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            title=f"{y_col} vs {x_col}",
            template="plotly_dark",
            trendline="ols"
        )
        
        return {
            "type": "scatter",
            "x_column": x_col,
            "y_column": y_col,
            "chart_json": fig.to_json()
        }


class ForecastAgent:
    """Performs time series forecasting."""
    
    @staticmethod
    def forecast_prophet(df: pd.DataFrame, date_col: str, value_col: str, periods: int = 30) -> dict[str, Any]:
        """Forecast using Prophet."""
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = df[[date_col, value_col]].copy()
        prophet_df.columns = ['ds', 'y']
        prophet_df = prophet_df.dropna()
        
        # Train model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        model.fit(prophet_df)
        
        # Make predictions
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        # Extract predictions
        predictions = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
        
        return {
            "model": "prophet",
            "periods": periods,
            "predictions": predictions.to_dict(orient="records"),
            "accuracy": {
                "mae": float(np.mean(np.abs(forecast['yhat'][:len(prophet_df)] - prophet_df['y']))),
            }
        }
