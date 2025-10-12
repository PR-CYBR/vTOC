from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Asset

router = APIRouter()

class AssetCreate(BaseModel):
    name: str
    asset_type: str
    status: str = "available"
    location: str = None
    specifications: dict = None
    assigned_to: str = None

class AssetResponse(BaseModel):
    id: int
    name: str
    asset_type: str
    status: str
    location: str = None
    specifications: dict = None
    assigned_to: str = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AssetResponse])
async def list_assets(asset_type: Optional[str] = None, db: Session = Depends(get_db)):
    """List all assets, optionally filtered by type"""
    query = db.query(Asset)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    assets = query.all()
    return assets

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get a specific asset by ID"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.post("/", response_model=AssetResponse)
async def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    """Create a new asset"""
    db_asset = Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: int, asset: AssetCreate, db: Session = Depends(get_db)):
    """Update an asset"""
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    for key, value in asset.dict().items():
        setattr(db_asset, key, value)
    
    db_asset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.delete("/{asset_id}")
async def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    """Delete an asset"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted successfully"}
