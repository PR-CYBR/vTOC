"""RF Engine FastAPI application.

FISSURE-class RF capabilities for vTOC (clean-room implementation, MIT licensed).
No GPL code copied - design guided by public documentation only.
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response

from .config import settings

# Prometheus metrics
capture_count = Counter("rf_captures_total", "Total number of RF captures started")
capture_active = Gauge("rf_captures_active", "Number of active captures")
capture_duration = Histogram("rf_capture_duration_seconds", "Capture duration")
classify_count = Counter("rf_classifications_total", "Total number of classifications")
tx_count = Counter("rf_tx_total", "Total number of TX operations")
tx_blocked = Counter("rf_tx_blocked_total", "Total number of blocked TX attempts")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup/shutdown tasks."""
    # Startup
    logger.info(f"🚀 RF Engine starting - Station: {settings.prcybr_station_id}")
    logger.info(f"   Division: {settings.prcybr_division}")
    logger.info(f"   TX Enabled: {settings.rf_tx_enabled}")
    logger.info(f"   Allowed Devices: {', '.join(settings.allowed_devices)}")

    if settings.rf_tx_enabled:
        logger.warning("⚠️  TX IS ENABLED - Ensure proper authorization and frequency whitelist")
        if settings.tx_whitelist_freqs:
            logger.info(
                f"   TX Whitelist: {[f'{f/1e6:.2f} MHz' for f in settings.tx_whitelist_freqs]}"
            )
        else:
            logger.error("   TX enabled but whitelist is empty - all TX will be blocked!")
    else:
        logger.info("   TX disabled (RX-only mode)")

    yield

    # Shutdown
    logger.info("🛑 RF Engine shutting down")


# Create FastAPI app
app = FastAPI(
    title="PR-CYBR RF Engine",
    description="FISSURE-class RF capabilities for vTOC (MIT licensed, clean-room implementation)",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level.upper(),
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "station_id": settings.prcybr_station_id,
        "division": settings.prcybr_division,
        "tx_enabled": str(settings.rf_tx_enabled),
    }


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/api/v2/rf/info")
def rf_info() -> dict[str, any]:
    """Get RF engine configuration and status."""
    return {
        "station_id": settings.prcybr_station_id,
        "division": settings.prcybr_division,
        "tx_enabled": settings.rf_tx_enabled,
        "tx_whitelist_freqs_mhz": [f / 1e6 for f in settings.tx_whitelist_freqs],
        "allowed_devices": settings.allowed_devices,
        "max_capture_seconds": settings.rf_max_capture_seconds,
        "version": "0.1.0",
    }


# Future router includes will go here:
# from .routers import devices, capture, classify, protocol, replay, archive
# app.include_router(devices.router)
# app.include_router(capture.router)
# app.include_router(classify.router)
# app.include_router(protocol.router)
# app.include_router(replay.router)
# app.include_router(archive.router)


def main() -> None:
    """Main entry point for running the RF Engine server."""
    import uvicorn

    uvicorn.run(
        "rfengine.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
