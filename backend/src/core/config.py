"""
Core configuration management for Aurix backend.
Uses pydantic-settings for environment validation and type safety.
"""
from typing import Literal
from functools import lru_cache
from pydantic import Field, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Aurix"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )
    
    # Database
    database_url: PostgresDsn
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False
    
    # Redis & Celery
    redis_url: RedisDsn
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    
    @validator("celery_broker_url", pre=True, always=True)
    def set_celery_broker(cls, v: str | None, values: dict) -> str:
        """Default celery broker to redis_url."""
        return v or str(values.get("redis_url"))
    
    @validator("celery_result_backend", pre=True, always=True)
    def set_celery_backend(cls, v: str | None, values: dict) -> str:
        """Default celery backend to redis_url."""
        return v or str(values.get("redis_url"))
    
    # Authentication (Supabase)
    supabase_url: str
    supabase_jwt_public_key: str
    supabase_service_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # Encryption
    encryption_key: str  # Fernet key for OAuth tokens
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.2
    openai_max_tokens: int = 2000
    
    # Integrations - Google OAuth (REQUIRED)
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/api/v1/datasources/oauth/google/callback"
    
    # Storage
    storage_provider: Literal["supabase", "s3", "local"] = "supabase"
    storage_bucket: str = "aurix-reports"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    
    # Caching
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # AI Analysis
    ai_summary_max_transactions: int = 1000
    ai_retry_attempts: int = 3
    ai_timeout_seconds: int = 30
    
    # Forecasting
    forecast_default_horizon_days: int = 90
    forecast_min_data_points: int = 30
    
    # Reports
    report_max_file_size_mb: int = 50
    
    # Feature Flags
    enable_google_sheets: bool = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded once and reused.
    """
    return Settings()


# Convenience export
settings = get_settings()
