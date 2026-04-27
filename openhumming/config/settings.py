from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OpenHumming"
    app_tagline: str = "Small agent. Full loop."
    host: str = "127.0.0.1"
    port: int = 8765
    workspace_root: Path = Field(default_factory=lambda: Path("workspace").resolve())
    provider: str = "local"
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    anthropic_model: str = "claude-3-5-haiku-latest"
    anthropic_api_key: str | None = None
    conversation_history_limit: int = 20
    log_level: str = "INFO"
    trace_enabled: bool = True
    scheduler_enabled: bool = True
    scheduler_timezone: str = "Asia/Shanghai"
    scheduler_sync_interval_seconds: int = 30
    daily_review_enabled: bool = True
    daily_review_hour: int = 23
    daily_review_minute: int = 0

    model_config = SettingsConfigDict(
        env_prefix="OPENHUMMING_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
