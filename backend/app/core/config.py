r"""
backend/app/core/config.py — Enterprise Configuration & Environment Validator
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application & Environment
    app_name: str = "AUTOPILOT API"
    app_version: str = "1.0.0"
    env: str = Field(default="development", alias="ENV")
    debug: bool = False
    port: int = Field(default=8765, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")
    secret_key: str = Field(default="autopilot-super-secure-production-secret-key-32chars", alias="APP_SECRET_KEY")
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8765",
        "https://app.autopilot.ai",
        "https://autopilot.ai"
    ]

    # Multi-tenant Database (PostgreSQL / SQLite fallback)
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")

    # Distributed Queue & Cache (Redis)
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    # Cloud Storage (Cloudflare R2 / AWS S3 / Local)
    storage_provider: str = Field(default="local", alias="STORAGE_PROVIDER")
    storage_endpoint: Optional[str] = Field(default=None, alias="STORAGE_ENDPOINT")
    storage_bucket: str = Field(default="autopilot-assets", alias="STORAGE_BUCKET")
    storage_access_key: Optional[str] = Field(default=None, alias="STORAGE_ACCESS_KEY")
    storage_secret_key: Optional[str] = Field(default=None, alias="STORAGE_SECRET_KEY")
    storage_public_base_url: Optional[str] = Field(default=None, alias="STORAGE_PUBLIC_BASE_URL")

    # AI Model Providers
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    moonshot_api_key: Optional[str] = Field(default=None, alias="MOONSHOT_API_KEY")

    # Text to Speech
    tts_provider: str = Field(default="edge", alias="TTS_PROVIDER")
    elevenlabs_api_key: Optional[str] = Field(default=None, alias="ELEVENLABS_API_KEY")

    # Billing & Payments
    billing_provider: str = Field(default="stripe", alias="BILLING_PROVIDER")
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")

    # Observability
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")

    # Meta / Instagram Professional Publishing
    meta_app_id: Optional[str] = Field(default=None, alias="META_APP_ID")
    meta_app_secret: Optional[str] = Field(default=None, alias="META_APP_SECRET")
    meta_redirect_uri: str = Field(default="http://localhost:8000/api/v1/integrations/instagram/oauth/callback", alias="META_REDIRECT_URI")
    meta_api_version: str = Field(default="v21.0", alias="META_API_VERSION")
    meta_graph_base_url: str = Field(default="https://graph.facebook.com", alias="META_GRAPH_BASE_URL")
    meta_oauth_dialog_url: str = Field(default="https://www.facebook.com", alias="META_OAUTH_DIALOG_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
