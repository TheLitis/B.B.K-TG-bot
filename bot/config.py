"""Application configuration for the Lgpol Telegram bot."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    """Runtime settings loaded from environment variables and defaults."""

    bot_token: SecretStr = Field(alias="BOT_TOKEN")
    manager_chat_id: int = Field(alias="MANAGER_CHAT_ID")
    webhook_url: str | None = Field(default=None, alias="WEBHOOK_URL")
    webapp_host: str | None = Field(default=None, alias="WEBAPP_HOST")
    webapp_port: int | None = Field(default=None, alias="WEBAPP_PORT")
    use_webhook: bool = Field(default=False, alias="USE_WEBHOOK")
    data_dir: Path = Field(default=BASE_DIR / "data")
    tmp_dir: Path = Field(default=BASE_DIR / "tmp")
    locale: str = Field(default="ru")
    autosave_selection: bool = Field(default=True, alias="AUTOSAVE_SELECTION")

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary of settings."""
        data = self.model_dump()
        data["bot_token"] = self.bot_token.get_secret_value()
        return data


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings."""

    dotenv_path = BASE_DIR / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
    else:
        load_dotenv()

    env_data = dict(os.environ)
    return Settings.model_validate(env_data)


__all__ = ["Settings", "get_settings", "BASE_DIR"]
