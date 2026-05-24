"""Application configuration management."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="Unified Social Media API", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    database_sync_url: str = Field(..., alias="DATABASE_SYNC_URL")
    
    # Redis & Celery (optional for now)
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    celery_broker_url: Optional[str] = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, alias="CELERY_RESULT_BACKEND")
    
    # Mock OAuth (ADD THIS LINE)
    mock_oauth: bool = Field(default=True, alias="MOCK_OAUTH")  # ← ADD THIS
    
    # OAuth credentials
    meta_app_id: Optional[str] = Field(default=None, alias="META_APP_ID")
    meta_app_secret: Optional[str] = Field(default=None, alias="META_APP_SECRET")
    meta_graph_api_version: str = Field(default="v18.0", alias="META_GRAPH_API_VERSION")
    
    twitter_api_key: Optional[str] = Field(default=None, alias="TWITTER_API_KEY")
    twitter_api_secret: Optional[str] = Field(default=None, alias="TWITTER_API_SECRET")
    twitter_bearer_token: Optional[str] = Field(default=None, alias="TWITTER_BEARER_TOKEN")
    
    linkedin_client_id: Optional[str] = Field(default=None, alias="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: Optional[str] = Field(default=None, alias="LINKEDIN_CLIENT_SECRET")
    
    whatsapp_phone_number_id: Optional[str] = Field(default=None, alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_access_token: Optional[str] = Field(default=None, alias="WHATSAPP_ACCESS_TOKEN")
    
    youtube_api_key: Optional[str] = Field(default=None, alias="YOUTUBE_API_KEY")
    youtube_client_id: Optional[str] = Field(default=None, alias="YOUTUBE_CLIENT_ID")
    youtube_client_secret: Optional[str] = Field(default=None, alias="YOUTUBE_CLIENT_SECRET")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # ←  - ignores any extra fields


settings = Settings()