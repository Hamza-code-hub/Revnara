from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "revnara-backend"
    environment: str = "local"
    version: str = "0.1.0"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/revnara"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    # HS256 shared secret, per docs/adr/0007-jwt-verification.md.
    supabase_jwt_secret: str = ""
    supabase_jwt_audience: str = "authenticated"

    # Sprint 4 (Company Brain): private bucket for tenant file uploads.
    # Per-tenant isolation is a path prefix within this one bucket (see
    # app/files/storage.py), enforced by both the backend's own path
    # construction and a Supabase Storage bucket policy (DB4.2).
    supabase_storage_bucket: str = "company-files"

    model_provider_api_key: str = ""
    model_provider_fallback_api_key: str = ""

    sentry_dsn: str = ""

    # BE3.6 tenant-aware rate limiting -- technical abuse protection,
    # independent of Sprint 15.6's plan-based entitlement limits.
    tenant_rate_limit_per_minute: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
