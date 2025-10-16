"""RSS and HTML telemetry scraper."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, List, Optional

import feedparser
import httpx
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from selectolax.parser import HTMLParser

logger = logging.getLogger("vtoc.scraper")
logging.basicConfig(level=logging.INFO)

load_dotenv()


class FeedLocation(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FeedConfig(BaseModel):
    name: str
    url: str
    tags: List[str] = Field(default_factory=list)
    location: FeedLocation = Field(default_factory=FeedLocation)
    selector: Optional[str] = None


class ScraperConfig(BaseModel):
    interval_seconds: int = 300
    feeds: List[FeedConfig]


async def fetch_rss(client: httpx.AsyncClient, feed: FeedConfig) -> list[dict[str, Any]]:
    logger.info("Fetching feed %s", feed.name)
    response = await client.get(feed.url, timeout=30)
    response.raise_for_status()
    parsed = feedparser.parse(response.text)
    events: list[dict[str, Any]] = []
    for entry in parsed.entries:
        payload = {
            "title": getattr(entry, "title", "Unknown"),
            "summary": getattr(entry, "summary", ""),
            "link": getattr(entry, "link", ""),
            "tags": [tag.term for tag in getattr(entry, "tags", [])],
        }
        payload["tags"].extend(feed.tags)
        published = getattr(entry, "published_parsed", None)
        if published:
            timestamp = datetime(*published[:6]).isoformat()
        else:
            timestamp = datetime.utcnow().isoformat()
        events.append({
            "source": feed.name,
            "timestamp": timestamp,
            "payload": payload,
            "latitude": feed.location.latitude,
            "longitude": feed.location.longitude,
        })
    return events


async def fetch_html(client: httpx.AsyncClient, feed: FeedConfig) -> list[dict[str, Any]]:
    if not feed.selector:
        return []
    logger.info("Fetching HTML target for %s", feed.name)
    response = await client.get(feed.url, timeout=30)
    response.raise_for_status()
    parser = HTMLParser(response.text)
    nodes = parser.css(feed.selector)
    results = []
    for node in nodes:
        text = node.text(strip=True)
        if not text:
            continue
        results.append({
            "source": feed.name,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {"content": text, "selector": feed.selector},
            "latitude": feed.location.latitude,
            "longitude": feed.location.longitude,
        })
    return results


async def post_events(
    client: httpx.AsyncClient,
    events: list[dict[str, Any]],
    *,
    supabase_client: Optional[httpx.AsyncClient] = None,
    supabase_function: Optional[str] = None,
    supabase_table: Optional[str] = None,
) -> None:
    for event in events:
        slug = slugify(event["source"])
        payload = {
            "source_slug": slug,
            "source_name": event["source"],
            "event_time": event.get("timestamp"),
            "payload": event.get("payload"),
            "latitude": event.get("latitude"),
            "longitude": event.get("longitude"),
        }
        logger.debug("Posting event: %s", json.dumps(payload))

        if supabase_client:
            try:
                await send_event_to_supabase(
                    supabase_client,
                    payload,
                    function=supabase_function,
                    table=supabase_table,
                )
                continue
            except (httpx.HTTPError, ValueError) as exc:
                logger.error("Failed to send event to Supabase: %s", exc)

        try:
            response = await client.post("/api/v1/telemetry/events", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to send event: %s", exc)


async def run_iteration(config: ScraperConfig, base_url: str) -> None:
    supabase_url = getenv_str("SUPABASE_URL", "")
    supabase_service_key = getenv_str("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_function = os.getenv("SUPABASE_INGEST_FUNCTION")
    supabase_table = os.getenv("SUPABASE_TELEMETRY_TABLE", "telemetry_events")

    async with httpx.AsyncClient(base_url=base_url) as client:
        supabase_client: Optional[httpx.AsyncClient] = None
        if supabase_url and supabase_service_key:
            headers = {
                "apikey": supabase_service_key,
                "Authorization": f"Bearer {supabase_service_key}",
                "Content-Type": "application/json",
            }
            supabase_client = httpx.AsyncClient(base_url=supabase_url, headers=headers)

        try:
            for feed in config.feeds:
                rss_events = await fetch_rss(client, feed)
                html_events = await fetch_html(client, feed)
                await post_events(
                    client,
                    rss_events + html_events,
                    supabase_client=supabase_client,
                    supabase_function=supabase_function,
                    supabase_table=supabase_table,
                )
        finally:
            if supabase_client:
                await supabase_client.aclose()


async def main() -> None:
    config_path = "config.yaml"
    with open(config_path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    config = ScraperConfig.model_validate(raw)
    backend_url = getenv_str("BACKEND_BASE_URL", "http://localhost:8080")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_iteration, "interval", seconds=config.interval_seconds, args=[config, backend_url])
    scheduler.start()

    logger.info("Scraper started with interval %s seconds", config.interval_seconds)
    try:
        await run_iteration(config, backend_url)
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down scraper")
        scheduler.shutdown()


def getenv_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


def slugify(value: str) -> str:
    return "-".join(value.lower().split())


async def send_event_to_supabase(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
    *,
    function: Optional[str],
    table: Optional[str],
) -> None:
    if function:
        endpoint = f"/functions/v1/{function.lstrip('/')}"
        response = await client.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        return

    if table:
        endpoint = f"/rest/v1/{table}"
        response = await client.post(
            endpoint,
            json=payload,
            headers={"Prefer": "return=minimal"},
            timeout=30,
        )
        response.raise_for_status()
        return

    raise ValueError("Supabase function or table must be configured for ingestion")


if __name__ == "__main__":
    asyncio.run(main())
