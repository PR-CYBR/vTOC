"""Database configuration and session utilities."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Generator, Optional, Tuple

from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from .config import get_settings

Base = declarative_base()

ENGINE_BY_STATION: Dict[str, Engine] = {}
SESSION_FACTORY_BY_STATION: Dict[str, sessionmaker] = {}
SUPABASE_CLIENT: Client | None = None


def _connection_settings_for_station(slug: str | None) -> Tuple[str, bool]:
    settings = get_settings()
    if not slug:
        return settings.default_database_url, settings.using_supabase_default

    slug_lower = slug.lower()
    overrides = settings.station_database_overrides
    if slug_lower in overrides:
        return overrides[slug_lower], settings.is_supabase_station(slug_lower)

    raise HTTPException(status_code=404, detail=f"Unknown station context: {slug}")


def _create_engine(url: str, *, supabase: bool) -> Engine:
    settings = get_settings()
    engine_kwargs = {"future": True, "pool_pre_ping": True}
    if supabase:
        overflow = max(
            settings.supabase_pool_max_connections - settings.supabase_pool_min_connections,
            0,
        )
        engine_kwargs.update(
            {
                "poolclass": QueuePool,
                "pool_size": settings.supabase_pool_min_connections,
                "max_overflow": overflow,
                "pool_timeout": settings.supabase_pool_timeout_seconds,
                "connect_args": {"sslmode": "require"},
            }
        )
    return create_engine(url, **engine_kwargs)


def _initialise_supabase_client() -> None:
    global SUPABASE_CLIENT
    if SUPABASE_CLIENT is not None:
        return

    settings = get_settings()
    if not settings.supabase_enabled:
        return

    SUPABASE_CLIENT = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=ClientOptions(
            postgrest_client_timeout=settings.supabase_pool_timeout_seconds,
        ),
    )


def _initialise_engines() -> None:
    global ENGINE_BY_STATION, SESSION_FACTORY_BY_STATION

    if ENGINE_BY_STATION:
        return

    default_url, is_supabase = _connection_settings_for_station(None)
    default_engine = _create_engine(default_url, supabase=is_supabase)
    ENGINE_BY_STATION["default"] = default_engine
    SESSION_FACTORY_BY_STATION["default"] = sessionmaker(
        bind=default_engine, autoflush=False, autocommit=False, future=True
    )

    settings = get_settings()
    for slug, url in settings.station_database_overrides.items():
        engine = _create_engine(url, supabase=settings.is_supabase_station(slug))
        ENGINE_BY_STATION[slug] = engine
        SESSION_FACTORY_BY_STATION[slug] = sessionmaker(
            bind=engine, autoflush=False, autocommit=False, future=True
        )


_initialise_engines()
_initialise_supabase_client()


def get_session_factory(station_slug: Optional[str] = None) -> sessionmaker:
    if not station_slug:
        return SESSION_FACTORY_BY_STATION["default"]

    slug = station_slug.lower()
    if slug not in SESSION_FACTORY_BY_STATION:
        url, is_supabase = _connection_settings_for_station(slug)
        engine = _create_engine(url, supabase=is_supabase)
        ENGINE_BY_STATION[slug] = engine
        SESSION_FACTORY_BY_STATION[slug] = sessionmaker(
            bind=engine, autoflush=False, autocommit=False, future=True
        )

    return SESSION_FACTORY_BY_STATION[slug]


@contextmanager
def session_scope(station_slug: Optional[str] = None) -> Generator[Session, None, None]:
    session_local = get_session_factory(station_slug)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


def _resolve_station_slug(request: Request) -> Optional[str]:
    candidate_headers = (
        "x-station-id",
        "x-station-slug",
        "x-chatkit-station",
        "x-toc-station",
    )

    for header in candidate_headers:
        value = request.headers.get(header)
        if not value:
            continue
        slug = value.replace("_", "-").lower()
        if slug in SESSION_FACTORY_BY_STATION:
            return slug
    return None


def get_db(station_slug: Optional[str] = None) -> Generator[Session, None, None]:
    with session_scope(station_slug) as session:
        yield session


def get_station_db(request: Request) -> Generator[Session, None, None]:
    station_slug = _resolve_station_slug(request)
    with session_scope(station_slug) as session:
        yield session


__all__ = [
    "Base",
    "ENGINE_BY_STATION",
    "SESSION_FACTORY_BY_STATION",
    "SUPABASE_CLIENT",
    "get_db",
    "get_station_db",
    "get_session_factory",
    "_initialise_supabase_client",
    "session_scope",
]
