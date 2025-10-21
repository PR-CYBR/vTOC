"""Helpers for resolving station context from HTTP requests."""
from __future__ import annotations

from typing import Iterable, Mapping, Optional

STATION_HEADER_CANDIDATES = (
    "x-station-id",
    "x-station-slug",
    "x-chatkit-station",
    "x-toc-station",
)


def _normalise_slug(value: str) -> str:
    """Normalise a station slug value from headers."""
    return value.replace("_", "-").lower()


def resolve_station_slug(
    headers: Mapping[str, str], known_slugs: Optional[Iterable[str]]
) -> Optional[str]:
    """Resolve the station slug from the provided headers.

    Args:
        headers: A mapping of header names to values.
        known_slugs: An optional iterable of slugs that are considered valid.

    Returns:
        The normalised station slug if one can be determined, otherwise ``None``.
    """

    allowed_slugs = None
    if known_slugs is not None:
        allowed_slugs = {slug.lower() for slug in known_slugs}

    for header in STATION_HEADER_CANDIDATES:
        value = headers.get(header)
        if not value:
            continue
        slug = _normalise_slug(value)
        if not slug:
            continue
        if allowed_slugs is not None and slug not in allowed_slugs:
            continue
        return slug
    return None


__all__ = [
    "STATION_HEADER_CANDIDATES",
    "resolve_station_slug",
]
