from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import engine, get_db, Base
from app.routers import operations, missions, assets, intel, agents
from app.models import Operation, Mission, Asset, IntelReport

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="vTOC API",
    description="Virtual Tactical Operations Center API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(operations.router, prefix="/api/operations", tags=["operations"])
app.include_router(missions.router, prefix="/api/missions", tags=["missions"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(intel.router, prefix="/api/intel", tags=["intelligence"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "vTOC API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "vTOC Backend API"
    }

@app.get("/api/metrics")
async def metrics():
    """Metrics endpoint for monitoring"""
    return {
        "service": "vtoc-backend",
        "endpoints": [
            "/api/operations",
            "/api/missions",
            "/api/assets",
            "/api/intel",
            "/api/agents"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
