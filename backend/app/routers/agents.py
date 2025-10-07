from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Agent

router = APIRouter()

class AgentCreate(BaseModel):
    name: str
    agent_type: str
    description: str = None
    configuration: dict = None

class AgentResponse(BaseModel):
    id: int
    name: str
    agent_type: str
    status: str
    description: str = None
    configuration: dict = None
    last_run: datetime = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AgentResponse])
async def list_agents(db: Session = Depends(get_db)):
    """List all agents"""
    agents = db.query(Agent).all()
    return agents

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get a specific agent by ID"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent"""
    db_agent = Agent(**agent.dict())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.post("/{agent_id}/start")
async def start_agent(agent_id: int, db: Session = Depends(get_db)):
    """Start an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.status = "running"
    agent.last_run = datetime.utcnow()
    db.commit()
    return {"message": f"Agent {agent.name} started", "status": agent.status}

@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: int, db: Session = Depends(get_db)):
    """Stop an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.status = "stopped"
    db.commit()
    return {"message": f"Agent {agent.name} stopped", "status": agent.status}

@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """Delete an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted successfully"}
