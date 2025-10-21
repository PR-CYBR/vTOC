"""Station-scoped routers."""
from fastapi import APIRouter

from . import agentkit, dashboard, tasks, timeline

router = APIRouter()
router.include_router(dashboard.router)
router.include_router(tasks.router)
router.include_router(agentkit.router)
router.include_router(timeline.router)

__all__ = ["router", "dashboard", "tasks", "agentkit", "timeline"]
