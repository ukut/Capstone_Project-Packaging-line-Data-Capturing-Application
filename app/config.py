"""Application configuration loaded from environment.

Centralizing config via pydantic-settings gives us:
- Type-checked env vars at startup (fail fast, not at first request)
- A single import surface for the rest of the app
- Easy override in tests via environment or .env files
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Loaded once at app startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_secret_key: str = "dev-only-replace-in-production"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "sqlite:///./bottling.db"

    # Session
    session_lifetime_minutes: int = 480  # 8-hour shift
    session_cookie_name: str = "bottling_session"
    session_cookie_secure: bool = False

    # Anomaly thresholds
    anomaly_downtime_minutes_threshold: int = 30
    anomaly_reject_rate_percent_threshold: float = 2.0

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Returns cached settings instance. Singleton via lru_cache."""
    return Settings()
