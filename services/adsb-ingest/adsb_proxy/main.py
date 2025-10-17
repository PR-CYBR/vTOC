"""FastAPI application exposing ADS-B proxy endpoints."""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI

from .config import Settings
from .proxy import AircraftProxy

settings = Settings.from_env()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(title="ADS-B Ingest Proxy", version="0.1.0")
proxy = AircraftProxy(settings)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting ADS-B ingest proxy")
    await proxy.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Stopping ADS-B ingest proxy")
    await proxy.stop()


@app.get("/aircraft.json", response_model=None)
async def get_aircraft() -> Dict[str, Any]:
    return await proxy.get_snapshot()


@app.get("/healthz")
async def get_health() -> Dict[str, Any]:
    status = proxy.health()
    payload: Dict[str, Any] = {
        "status": status.status,
        "last_update": status.last_update.isoformat() if status.last_update else None,
        "last_push": status.last_push.isoformat() if status.last_push else None,
    }
    if status.error:
        payload["error"] = status.error
    return payload


@app.get("/readyz")
async def readiness() -> Dict[str, Any]:
    status = proxy.health()
    healthy = status.status in {"ok", "initializing"}
    return {
        "status": "ok" if healthy else "stale",
        "last_update": status.last_update.isoformat() if status.last_update else None,
    }


def main() -> None:
    """Entry point for running under `python -m`."""
    import uvicorn

    uvicorn.run(
        "adsb_proxy.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
