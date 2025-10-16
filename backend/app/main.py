"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import agent_actions, telemetry
from .routers.stations import router as stations_router

app = FastAPI(title="vTOC API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(agent_actions.router)
app.include_router(stations_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
