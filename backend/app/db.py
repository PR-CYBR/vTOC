"""Database configuration and session utilities."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Dict, Generator, Iterable, Optional

from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc",
)

Base = declarative_base()


def _snake_to_slug(value: str) -> str:
    return value.replace("DATABASE_URL_", "").replace("_", "-").lower()


def _load_station_urls(env: Iterable[tuple[str, str]]) -> Dict[str, str]:
    stations: Dict[str, str] = {}
    for key, value in env:
        if not key.startswith("DATABASE_URL_TOC_"):
            continue
        slug = _snake_to_slug(key)
        stations[slug] = value
    return stations


def _create_engine(url: str) -> Engine:
    return create_engine(url, future=True)


ENGINE_BY_STATION: Dict[str, Engine] = {}
SESSION_FACTORY_BY_STATION: Dict[str, sessionmaker] = {}


def _initialise_engines() -> None:
    global ENGINE_BY_STATION, SESSION_FACTORY_BY_STATION

    if ENGINE_BY_STATION:
        return

    default_engine = _create_engine(DEFAULT_DATABASE_URL)
    ENGINE_BY_STATION["default"] = default_engine
    SESSION_FACTORY_BY_STATION["default"] = sessionmaker(
        bind=default_engine, autoflush=False, autocommit=False, future=True
    )

    for slug, url in _load_station_urls(os.environ.items()).items():
        engine = _create_engine(url)
        ENGINE_BY_STATION[slug] = engine
        SESSION_FACTORY_BY_STATION[slug] = sessionmaker(
            bind=engine, autoflush=False, autocommit=False, future=True
        )


_initialise_engines()


def get_session_factory(station_slug: Optional[str] = None) -> sessionmaker:
    if not station_slug:
        return SESSION_FACTORY_BY_STATION["default"]

    slug = station_slug.lower()
    if slug in SESSION_FACTORY_BY_STATION:
        return SESSION_FACTORY_BY_STATION[slug]

    raise HTTPException(status_code=404, detail=f"Unknown station context: {station_slug}")


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
    "get_db",
    "get_station_db",
    "get_session_factory",
    "session_scope",
]
