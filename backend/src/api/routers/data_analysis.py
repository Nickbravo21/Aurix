"""
Data Analysis API Routes
Upload, analyze, visualize, and query datasets with AI.
"""
import io
from typing import Annotated, Optional
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.db.session import get_session
from src.db.models import User, Tenant, Dataset, Analysis, InsightQuery, AnalysisReport, Prediction
from src.api.deps import get_current_user, get_current_tenant
from src.services.data_agents import (
    DataCleanerAgent,
    StatsAgent,
    InsightAgent,
    VizAgent,
    ForecastAgent
)
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/data", tags=["Data Analysis"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DatasetUploadResponse(BaseModel):
    dataset_id: UUID
    name: str
    row_count: int
    column_count: int
    columns: list[dict]
    status: str


class AnalysisRequest(BaseModel):
    dataset_id: UUID
    analysis_type: str  # descriptive|correlation|regression|outlier
    target_column: Optional[str] = None
    feature_columns: Optional[list[str]] = None


class AnalysisResponse(BaseModel):
    analysis_id: UUID
    dataset_id: UUID
    analysis_type: str
    results: dict
    insights: Optional[str] = None
    charts: list[dict]


class QuestionRequest(BaseModel):
    dataset_id: UUID
    question: str


class QuestionResponse(BaseModel):
    query_id: UUID
    question: str
    answer: str
    charts: list[dict]


class ForecastRequest(BaseModel):
    dataset_id: UUID
    date_column: str
    value_column: str
    periods: int = 30
    model: str = "prophet"


class ReportRequest(BaseModel):
    dataset_id: UUID
    report_type: str = "full_analysis"
    include_charts: bool = True


# ============================================================================
# Dataset Upload & Management
# ============================================================================

@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Upload a dataset (CSV/Excel) for analysis.
    """
    logger.info(f"DEMO MODE: User {current_user.email} uploading dataset: {file.filename}")
    
    # Read file
    contents = await file.read()
    
    try:
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
            file_type = "csv"
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
            file_type = "excel"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Please upload CSV or Excel."
            )
        
        # Clean data
        df_clean, cleaning_report = DataCleanerAgent.clean_dataframe(df)
        
        # Detect column types
        columns_info = DataCleanerAgent.detect_column_types(df_clean)
        
        # Create dataset record
        dataset = Dataset(
            tenant_id=tenant.id,
            user_id=current_user.id,
            name=name or file.filename,
            file_type=file_type,
            file_size=len(contents),
            storage_path=f"datasets/{tenant.id}/{file.filename}",
            row_count=len(df_clean),
            column_count=len(df_clean.columns),
            columns=list(columns_info.values()),
            status="ready"
        )
        
        session.add(dataset)
        await session.commit()
        await session.refresh(dataset)
        
        logger.info(f"Dataset {dataset.id} uploaded successfully: {dataset.row_count} rows, {dataset.column_count} columns")
        
        return DatasetUploadResponse(
            dataset_id=dataset.id,
            name=dataset.name,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            columns=dataset.columns,
            status=dataset.status
        )
        
    except Exception as e:
        logger.error(f"Failed to upload dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process dataset: {str(e)}"
        )


@router.get("/datasets")
async def list_datasets(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """List all datasets for the tenant."""
    stmt = select(Dataset).where(Dataset.tenant_id == tenant.id).order_by(Dataset.created_at.desc())
    result = await session.execute(stmt)
    datasets = result.scalars().all()
    
    return {
        "datasets": [
            {
                "id": str(ds.id),
                "name": ds.name,
                "row_count": ds.row_count,
                "column_count": ds.column_count,
                "status": ds.status,
                "created_at": ds.created_at.isoformat()
            }
            for ds in datasets
        ]
    }


# ============================================================================
# Data Analysis
# ============================================================================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_dataset(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Perform statistical analysis on a dataset.
    """
    # Get dataset (in real implementation, load from storage)
    stmt = select(Dataset).where(Dataset.id == request.dataset_id, Dataset.tenant_id == tenant.id)
    result = await session.execute(stmt)
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # For demo, create sample data
    df = pd.DataFrame({
        'revenue': [45000, 52000, 48000, 55000, 61000, 58000],
        'expenses': [32000, 35000, 33000, 38000, 42000, 40000],
        'marketing_spend': [5000, 6000, 5500, 7000, 8000, 7500],
        'month': pd.date_range('2024-06-01', periods=6, freq='M')
    })
    
    # Perform analysis
    results = {}
    charts = []
    
    if request.analysis_type == "descriptive":
        results = StatsAgent.descriptive_stats(df)
        charts.append(VizAgent.create_correlation_heatmap(df))
        
    elif request.analysis_type == "correlation":
        results = StatsAgent.descriptive_stats(df)
        charts.append(VizAgent.create_correlation_heatmap(df))
        charts.append(VizAgent.create_scatter_plot(df, 'marketing_spend', 'revenue'))
        
    elif request.analysis_type == "regression" and request.target_column:
        features = request.feature_columns or [col for col in df.select_dtypes(include=['number']).columns if col != request.target_column]
        results = StatsAgent.regression_analysis(df, request.target_column, features)
        
    elif request.analysis_type == "outlier":
        results = StatsAgent.detect_outliers(df)
    
    # Generate AI insights
    insights = await InsightAgent.generate_insights(results, request.analysis_type)
    
    # Create analysis record
    analysis = Analysis(
        tenant_id=tenant.id,
        dataset_id=dataset.id,
        user_id=current_user.id,
        analysis_type=request.analysis_type,
        results=results,
        summary=insights,
        statistics=results.get("summary", {}),
        correlations=results.get("correlation", {}),
        charts=charts,
        status="completed"
    )
    
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    
    return AnalysisResponse(
        analysis_id=analysis.id,
        dataset_id=dataset.id,
        analysis_type=analysis.analysis_type,
        results=results,
        insights=insights,
        charts=charts
    )


# ============================================================================
# Natural Language Querying
# ============================================================================

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Ask a natural language question about the dataset.
    """
    # Get dataset
    stmt = select(Dataset).where(Dataset.id == request.dataset_id, Dataset.tenant_id == tenant.id)
    result = await session.execute(stmt)
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # For demo, create sample data
    df = pd.DataFrame({
        'revenue': [45000, 52000, 48000, 55000, 61000, 58000],
        'expenses': [32000, 35000, 33000, 38000, 42000, 40000],
        'marketing_spend': [5000, 6000, 5500, 7000, 8000, 7500],
        'month': pd.date_range('2024-06-01', periods=6, freq='M')
    })
    
    # Answer question with AI
    result = await InsightAgent.answer_question(df, request.question)
    
    # Create query record
    query = InsightQuery(
        tenant_id=tenant.id,
        dataset_id=dataset.id,
        user_id=current_user.id,
        query=request.question,
        query_type="custom",
        response=result["answer"],
        data_used=result.get("data_used", {})
    )
    
    session.add(query)
    await session.commit()
    await session.refresh(query)
    
    return QuestionResponse(
        query_id=query.id,
        question=request.question,
        answer=result["answer"],
        charts=[]
    )


# ============================================================================
# Forecasting
# ============================================================================

@router.post("/forecast")
async def forecast_data(
    request: ForecastRequest,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate forecast predictions using Prophet or ARIMA.
    """
    # Get dataset
    stmt = select(Dataset).where(Dataset.id == request.dataset_id, Dataset.tenant_id == tenant.id)
    result = await session.execute(stmt)
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # For demo, create sample time series data
    df = pd.DataFrame({
        request.date_column: pd.date_range('2024-01-01', periods=180, freq='D'),
        request.value_column: np.random.randn(180).cumsum() + 100
    })
    
    # Run forecast
    if request.model == "prophet":
        forecast_results = ForecastAgent.forecast_prophet(
            df, 
            request.date_column, 
            request.value_column, 
            request.periods
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported model type")
    
    # Generate insights
    insights = await InsightAgent.generate_insights(forecast_results, "forecast")
    
    # Create prediction record
    prediction = Prediction(
        tenant_id=tenant.id,
        dataset_id=dataset.id,
        analysis_id=UUID("00000000-0000-0000-0000-000000000001"),  # Demo
        model_type=request.model,
        target_variable=request.value_column,
        predictions=forecast_results["predictions"],
        forecast_period=request.periods,
        accuracy_metrics=forecast_results.get("accuracy", {}),
        insights=insights
    )
    
    session.add(prediction)
    await session.commit()
    await session.refresh(prediction)
    
    return {
        "prediction_id": str(prediction.id),
        "model": request.model,
        "forecast": forecast_results,
        "insights": insights
    }


# ============================================================================
# Report Generation
# ============================================================================

@router.post("/report")
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a comprehensive analysis report.
    """
    # Get dataset
    stmt = select(Dataset).where(Dataset.id == request.dataset_id, Dataset.tenant_id == tenant.id)
    result = await session.execute(stmt)
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create demo report
    report = AnalysisReport(
        tenant_id=tenant.id,
        dataset_id=dataset.id,
        user_id=current_user.id,
        title=f"Analysis Report: {dataset.name}",
        report_type=request.report_type,
        sections=[
            {
                "title": "Executive Summary",
                "content": "Dataset contains financial metrics showing positive growth trends."
            },
            {
                "title": "Key Findings",
                "content": "Revenue increased 35% over the period. Strong correlation between marketing spend and revenue."
            }
        ],
        insights=[
            "Revenue shows strong upward trend",
            "Marketing ROI is positive and improving",
            "Expenses are well-controlled relative to growth"
        ],
        recommendations=[
            "Continue current marketing strategy",
            "Consider increasing marketing budget by 20%",
            "Monitor expense ratios quarterly"
        ],
        charts=[]
    )
    
    session.add(report)
    await session.commit()
    await session.refresh(report)
    
    return {
        "report_id": str(report.id),
        "title": report.title,
        "sections": report.sections,
        "insights": report.insights,
        "recommendations": report.recommendations,
        "created_at": report.created_at.isoformat()
    }
