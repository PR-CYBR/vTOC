"""Application configuration helpers."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel, Field


class Settings(BaseModel):
    agentkit_api_base_url: str = Field(default="https://agentkit.example.com/api")
    agentkit_api_key: str = Field(default="", repr=False)
    agentkit_org_id: str = Field(default="")
    agentkit_timeout_seconds: float = Field(default=30.0)
    chatkit_webhook_secret: str = Field(default="", repr=False)
    chatkit_allowed_tools: List[str] = Field(default_factory=list)
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="", repr=False)
    supabase_schema: str = Field(default="public")
    supabase_timeout_seconds: float = Field(default=30.0)

    @property
    def is_agentkit_configured(self) -> bool:
        return bool(self.agentkit_api_key and self.agentkit_org_id)

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_KEY")
        or ""
    )
    return Settings(
        agentkit_api_base_url=os.getenv("AGENTKIT_API_BASE_URL", "https://agentkit.example.com/api"),
        agentkit_api_key=os.getenv("AGENTKIT_API_KEY", ""),
        agentkit_org_id=os.getenv("AGENTKIT_ORG_ID", ""),
        agentkit_timeout_seconds=float(os.getenv("AGENTKIT_TIMEOUT_SECONDS", "30")),
        chatkit_webhook_secret=os.getenv("CHATKIT_WEBHOOK_SECRET", ""),
        chatkit_allowed_tools=[
            value.strip()
            for value in os.getenv("CHATKIT_ALLOWED_TOOLS", "").split(",")
            if value.strip()
        ],
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=supabase_key,
        supabase_schema=os.getenv("SUPABASE_SCHEMA", "public"),
        supabase_timeout_seconds=float(os.getenv("SUPABASE_TIMEOUT_SECONDS", "30")),
    )


def reset_settings_cache() -> None:
    """Clear the cached settings to force reloads during tests."""
    get_settings.cache_clear()  # type: ignore[attr-defined]
