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
    supabase_jwt_secret: str = ""

    model_provider_api_key: str = ""
    model_provider_fallback_api_key: str = ""

    sentry_dsn: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
