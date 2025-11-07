"""
Database models for Aurix platform.
All models include tenant_id for multi-tenancy support.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Column, JSON, Index
from sqlalchemy import UniqueConstraint, CheckConstraint


# ============================================================================
# Tenant & User Models
# ============================================================================

class Tenant(SQLModel, table=True):
    """Organization/company using Aurix."""
    
    __tablename__ = "tenants"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    plan: str = Field(default="starter", max_length=50)  # starter|pro|enterprise
    status: str = Field(default="active", max_length=50)  # active|suspended|cancelled
    stripe_customer_id: Optional[str] = Field(default=None, max_length=255, index=True)
    stripe_subscription_id: Optional[str] = Field(default=None, max_length=255)
    
    # Limits based on plan
    max_datasources: int = Field(default=3)
    max_ai_calls_per_month: int = Field(default=1000)
    max_users: int = Field(default=5)
    
    # Usage tracking
    ai_calls_this_month: int = Field(default=0)
    last_ai_reset: datetime = Field(default_factory=datetime.utcnow)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_tenants_status_plan", "status", "plan"),
    )


class User(SQLModel, table=True):
    """User account linked to a tenant."""
    
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    
    email: str = Field(max_length=255, index=True)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="member", max_length=50)  # admin|member|viewer
    
    # Supabase auth integration
    auth_provider_id: str = Field(max_length=255, unique=True, index=True)
    auth_provider: str = Field(default="supabase", max_length=50)
    
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
        Index("ix_users_tenant_role", "tenant_id", "role"),
    )


# ============================================================================
# Data Source Models
# ============================================================================

class DataSource(SQLModel, table=True):
    """External data source connection (Google Sheets, QuickBooks, Stripe)."""
    
    __tablename__ = "datasources"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    
    kind: str = Field(max_length=50, index=True)  # google_sheets|quickbooks|stripe|plaid
    display_name: str = Field(max_length=255)
    status: str = Field(default="active", max_length=50)  # active|error|disconnected
    
    # Connection metadata
    config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Sync tracking
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_error: Optional[str] = None
    sync_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_datasources_tenant_kind", "tenant_id", "kind"),
        Index("ix_datasources_status", "status"),
    )


class OAuthToken(SQLModel, table=True):
    """Encrypted OAuth tokens for data source authentication."""
    
    __tablename__ = "oauth_tokens"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    data_source_id: UUID = Field(foreign_key="datasources.id", unique=True, index=True)
    
    # Encrypted tokens
    access_token: str = Field(max_length=2048)  # Encrypted
    refresh_token: Optional[str] = Field(default=None, max_length=2048)  # Encrypted
    
    expires_at: Optional[datetime] = None
    token_type: str = Field(default="Bearer", max_length=50)
    scope: Optional[str] = Field(default=None, max_length=1024)
    
    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Financial Data Models
# ============================================================================

class Account(SQLModel, table=True):
    """Chart of accounts."""
    
    __tablename__ = "accounts"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    
    name: str = Field(max_length=255)
    account_type: str = Field(max_length=50, index=True)  # asset|liability|income|expense|equity
    subtype: Optional[str] = Field(default=None, max_length=100)
    
    # Link to external system
    external_id: Optional[str] = Field(default=None, max_length=255)
    data_source_id: Optional[UUID] = Field(default=None, foreign_key="datasources.id")
    
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_accounts_tenant_type", "tenant_id", "account_type"),
        UniqueConstraint("tenant_id", "data_source_id", "external_id", name="uq_account_external"),
    )


class Transaction(SQLModel, table=True):
    """Financial transactions."""
    
    __tablename__ = "transactions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    account_id: Optional[UUID] = Field(default=None, foreign_key="accounts.id", index=True)
    
    date: date = Field(index=True)
    amount: Decimal = Field(max_digits=14, decimal_places=2)
    
    # Categorization
    category: Optional[str] = Field(default=None, max_length=100, index=True)
    subcategory: Optional[str] = Field(default=None, max_length=100)
    
    description: Optional[str] = Field(default=None, max_length=1024)
    memo: Optional[str] = Field(default=None, max_length=1024)
    
    # Source tracking
    data_source_id: UUID = Field(foreign_key="datasources.id", index=True)
    external_id: str = Field(max_length=255)
    
    # Raw data for debugging
    raw: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_transactions_tenant_date", "tenant_id", "date"),
        Index("ix_transactions_tenant_category", "tenant_id", "category"),
        UniqueConstraint("tenant_id", "data_source_id", "external_id", name="uq_transaction_external"),
    )


# ============================================================================
# Analytics Models
# ============================================================================

class MetricDaily(SQLModel, table=True):
    """Daily aggregated metrics (KPIs)."""
    
    __tablename__ = "metrics_daily"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    
    date: date = Field(index=True)
    metric: str = Field(max_length=100, index=True)  # revenue|expenses|net_cash|runway|etc
    value: Decimal = Field(max_digits=14, decimal_places=2)
    
    # Additional context
    metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "date", "metric", name="uq_metric_daily"),
        Index("ix_metrics_tenant_metric_date", "tenant_id", "metric", "date"),
    )


class Forecast(SQLModel, table=True):
    """AI-generated forecasts."""
    
    __tablename__ = "forecasts"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    
    metric: str = Field(max_length=100, index=True)
    horizon_days: int = Field(default=90)
    
    # Forecast data
    series: dict[str, Any] = Field(sa_column=Column(JSON))  # {date: value, ...}
    confidence_intervals: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Model metadata
    model_type: str = Field(default="prophet", max_length=50)
    model_params: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    accuracy_score: Optional[float] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_forecasts_tenant_metric", "tenant_id", "metric"),
    )


# ============================================================================
# Report Models
# ============================================================================

class Report(SQLModel, table=True):
    """Generated financial reports."""
    
    __tablename__ = "reports"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    created_by: UUID = Field(foreign_key="users.id")
    
    title: str = Field(max_length=255)
    report_type: str = Field(max_length=50)  # monthly|quarterly|annual|custom
    
    period_start: date
    period_end: date
    
    # Content
    html: str  # HTML version
    pdf_url: Optional[str] = Field(default=None, max_length=1024)  # S3/Supabase URL
    
    # AI summary
    ai_summary: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Access tracking
    view_count: int = Field(default=0)
    last_viewed_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_reports_tenant_created", "tenant_id", "created_at"),
    )


# ============================================================================
# Alert Models
# ============================================================================

class AlertRule(SQLModel, table=True):
    """Alert rules for notifications."""
    
    __tablename__ = "alert_rules"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    created_by: UUID = Field(foreign_key="users.id")
    
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1024)
    
    # Condition (e.g., "runway < 90", "expenses > 10000")
    metric: str = Field(max_length=100)
    operator: str = Field(max_length=20)  # <|>|<=|>=|==
    threshold: Decimal = Field(max_digits=14, decimal_places=2)
    
    # Notification settings
    channel: str = Field(max_length=50)  # slack|email|webhook
    target: str = Field(max_length=512)  # Channel ID, email, or webhook URL
    
    enabled: bool = Field(default=True)
    
    # Tracking
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_alerts_tenant_enabled", "tenant_id", "enabled"),
    )


class AlertLog(SQLModel, table=True):
    """Log of triggered alerts."""
    
    __tablename__ = "alert_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    alert_rule_id: UUID = Field(foreign_key="alert_rules.id", index=True)
    
    triggered_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Values at time of trigger
    metric_value: Decimal = Field(max_digits=14, decimal_places=2)
    threshold_value: Decimal = Field(max_digits=14, decimal_places=2)
    
    # Notification result
    sent_successfully: bool = Field(default=False)
    error_message: Optional[str] = None
    
    __table_args__ = (
        Index("ix_alert_logs_tenant_triggered", "tenant_id", "triggered_at"),
    )


# ============================================================================
# Audit Log
# ============================================================================

class AuditLog(SQLModel, table=True):
    """Audit trail for compliance and debugging."""
    
    __tablename__ = "audit_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    
    action: str = Field(max_length=100, index=True)  # user.login|report.generate|etc
    resource_type: Optional[str] = Field(default=None, max_length=50)
    resource_id: Optional[UUID] = None
    
    # Request details
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=512)
    
    # Context
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_audit_tenant_action", "tenant_id", "action", "created_at"),
    )


# ============================================================================
# AI Data Analysis Models
# ============================================================================

class Dataset(SQLModel, table=True):
    """Uploaded dataset for analysis."""
    
    __tablename__ = "datasets"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    file_type: str = Field(max_length=50)  # csv|excel|json
    file_size: int  # bytes
    storage_path: str = Field(max_length=512)  # S3/local path
    
    # Data metadata
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Processing status
    status: str = Field(default="uploaded", max_length=50)  # uploaded|processing|ready|error
    processing_error: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_datasets_tenant_status", "tenant_id", "status"),
    )


class Analysis(SQLModel, table=True):
    """Statistical analysis performed on a dataset."""
    
    __tablename__ = "analyses"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    dataset_id: UUID = Field(foreign_key="datasets.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    analysis_type: str = Field(max_length=100)  # descriptive|correlation|regression|forecast|outlier
    
    # Analysis results
    results: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    summary: Optional[str] = None  # AI-generated summary
    
    # Statistics
    statistics: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    correlations: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Visualizations
    charts: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Processing
    status: str = Field(default="pending", max_length=50)  # pending|processing|completed|error
    processing_time: Optional[float] = None  # seconds
    error: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    __table_args__ = (
        Index("ix_analyses_dataset_type", "dataset_id", "analysis_type"),
    )


class Prediction(SQLModel, table=True):
    """Forecasting and prediction results."""
    
    __tablename__ = "predictions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    dataset_id: UUID = Field(foreign_key="datasets.id", index=True)
    analysis_id: UUID = Field(foreign_key="analyses.id", index=True)
    
    model_type: str = Field(max_length=100)  # prophet|arima|linear_regression|neural_prophet
    target_variable: str = Field(max_length=255)
    
    # Prediction results
    predictions: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    forecast_period: int  # number of periods predicted
    
    # Model performance
    accuracy_metrics: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    confidence_intervals: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # AI insights
    insights: Optional[str] = None
    recommendations: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_predictions_dataset_model", "dataset_id", "model_type"),
    )


class InsightQuery(SQLModel, table=True):
    """Natural language queries and AI responses."""
    
    __tablename__ = "insight_queries"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    dataset_id: UUID = Field(foreign_key="datasets.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    query: str  # Natural language question
    query_type: str = Field(max_length=100)  # correlation|prediction|comparison|summary|custom
    
    # AI Response
    response: str  # AI-generated answer
    sql_executed: Optional[str] = None  # If SQL was generated
    data_used: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Charts generated
    charts: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Metadata
    processing_time: Optional[float] = None
    ai_model: str = Field(default="gpt-4o", max_length=50)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_queries_dataset_created", "dataset_id", "created_at"),
    )


class AnalysisReport(SQLModel, table=True):
    """Generated analysis reports with insights and visualizations."""
    
    __tablename__ = "analysis_reports"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    dataset_id: UUID = Field(foreign_key="datasets.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    title: str = Field(max_length=255)
    report_type: str = Field(max_length=100)  # full_analysis|executive_summary|custom
    
    # Report content
    sections: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    insights: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    recommendations: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Visualizations
    charts: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Export
    pdf_path: Optional[str] = None
    export_format: str = Field(default="pdf", max_length=50)  # pdf|html|markdown
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_reports_dataset_created", "dataset_id", "created_at"),
    )

