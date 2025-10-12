from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Mission

router = APIRouter()

class MissionCreate(BaseModel):
    operation_id: int
    name: str
    description: str = None
    status: str = "pending"
    priority: str = "medium"
    assigned_to: str = None

class MissionResponse(BaseModel):
    id: int
    operation_id: int
    name: str
    description: str = None
    status: str
    priority: str
    assigned_to: str = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[MissionResponse])
async def list_missions(operation_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all missions, optionally filtered by operation"""
    query = db.query(Mission)
    if operation_id:
        query = query.filter(Mission.operation_id == operation_id)
    missions = query.all()
    return missions

@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: int, db: Session = Depends(get_db)):
    """Get a specific mission by ID"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@router.post("/", response_model=MissionResponse)
async def create_mission(mission: MissionCreate, db: Session = Depends(get_db)):
    """Create a new mission"""
    db_mission = Mission(**mission.dict())
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    return db_mission

@router.put("/{mission_id}", response_model=MissionResponse)
async def update_mission(mission_id: int, mission: MissionCreate, db: Session = Depends(get_db)):
    """Update a mission"""
    db_mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    for key, value in mission.dict().items():
        setattr(db_mission, key, value)
    
    db_mission.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_mission)
    return db_mission

@router.delete("/{mission_id}")
async def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Delete a mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    db.delete(mission)
    db.commit()
    return {"message": "Mission deleted successfully"}
