"""Application configuration loaded from the environment."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for Market Radar."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"
    timezone: str = "Asia/Kolkata"
    top_n: int = 10
    universe_csv_path: Path = Path("data/reference/nifty500.csv")
    min_success_ratio: float = 0.8
    discord_webhook_url: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
