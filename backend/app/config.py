"""Application configuration helpers."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List

from pydantic import BaseModel, Field


def _collect_station_urls(prefix: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        slug = key.replace(prefix, "").replace("_", "-").lower()
        mapping[slug] = value
    return mapping


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

    database_url: str = Field(
        default="postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc"
    )
    supabase_db_url: str | None = Field(default=None)
    supabase_url: str | None = Field(default=None)
    supabase_service_role_key: str | None = Field(default=None, repr=False)
    supabase_pool_min_connections: int = Field(default=1)
    supabase_pool_max_connections: int = Field(default=10)
    supabase_pool_timeout_seconds: int = Field(default=30)
    station_database_urls: Dict[str, str] = Field(default_factory=dict)
    station_supabase_database_urls: Dict[str, str] = Field(default_factory=dict)

    @property
    def is_agentkit_configured(self) -> bool:
        return bool(self.agentkit_api_key and self.agentkit_org_id)

    @property
    def default_database_url(self) -> str:
        return self.supabase_db_url or self.database_url

    @property
    def using_supabase_default(self) -> bool:
        return bool(self.supabase_db_url)

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def station_database_overrides(self) -> Dict[str, str]:
        overrides = dict(self.station_database_urls)
        overrides.update(self.station_supabase_database_urls)
        return overrides

    def is_supabase_station(self, slug: str) -> bool:
        return slug in self.station_supabase_database_urls


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    pool_min = int(os.getenv("SUPABASE_POOL_MIN_CONNECTIONS", "1"))
    pool_max = int(os.getenv("SUPABASE_POOL_MAX_CONNECTIONS", "10"))
    pool_timeout = int(os.getenv("SUPABASE_POOL_TIMEOUT_SECONDS", "30"))
    if pool_max < pool_min:
        pool_max = pool_min

    return Settings(
        agentkit_api_base_url=os.getenv(
            "AGENTKIT_API_BASE_URL", "https://agentkit.example.com/api"
        ),
        agentkit_api_key=os.getenv("AGENTKIT_API_KEY", ""),
        agentkit_org_id=os.getenv("AGENTKIT_ORG_ID", ""),
        agentkit_timeout_seconds=float(os.getenv("AGENTKIT_TIMEOUT_SECONDS", "30")),
        chatkit_webhook_secret=os.getenv("CHATKIT_WEBHOOK_SECRET", ""),
        chatkit_allowed_tools=[
            value.strip()
            for value in os.getenv("CHATKIT_ALLOWED_TOOLS", "").split(",")
            if value.strip()
        ],
        database_url=os.getenv(
            "DATABASE_URL", "postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc"
        ),
        supabase_db_url=os.getenv("SUPABASE_DB_URL"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        supabase_pool_min_connections=pool_min,
        supabase_pool_max_connections=pool_max,
        supabase_pool_timeout_seconds=pool_timeout,
        station_database_urls=_collect_station_urls("DATABASE_URL_TOC_"),
        station_supabase_database_urls=_collect_station_urls("SUPABASE_DB_URL_TOC_"),
    )


def reset_settings_cache() -> None:
    """Clear the cached settings to force reloads during tests."""
    get_settings.cache_clear()  # type: ignore[attr-defined]
