from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import IntelReport

router = APIRouter()

class IntelReportCreate(BaseModel):
    mission_id: int = None
    title: str
    content: str
    classification: str = "unclassified"
    source: str = None
    reliability: str = None
    reported_by: str = None

class IntelReportResponse(BaseModel):
    id: int
    mission_id: int = None
    title: str
    content: str
    classification: str
    source: str = None
    reliability: str = None
    reported_by: str = None
    report_date: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[IntelReportResponse])
async def list_intel_reports(mission_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all intelligence reports, optionally filtered by mission"""
    query = db.query(IntelReport)
    if mission_id:
        query = query.filter(IntelReport.mission_id == mission_id)
    reports = query.all()
    return reports

@router.get("/{report_id}", response_model=IntelReportResponse)
async def get_intel_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific intelligence report by ID"""
    report = db.query(IntelReport).filter(IntelReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Intelligence report not found")
    return report

@router.post("/", response_model=IntelReportResponse)
async def create_intel_report(report: IntelReportCreate, db: Session = Depends(get_db)):
    """Create a new intelligence report"""
    db_report = IntelReport(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@router.delete("/{report_id}")
async def delete_intel_report(report_id: int, db: Session = Depends(get_db)):
    """Delete an intelligence report"""
    report = db.query(IntelReport).filter(IntelReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Intelligence report not found")
    
    db.delete(report)
    db.commit()
    return {"message": "Intelligence report deleted successfully"}
