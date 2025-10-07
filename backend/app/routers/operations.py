from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Operation

router = APIRouter()

class OperationCreate(BaseModel):
    name: str
    code_name: str
    description: str = None
    status: str = "planning"
    priority: str = "medium"

class OperationResponse(BaseModel):
    id: int
    name: str
    code_name: str
    description: str = None
    status: str
    priority: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[OperationResponse])
async def list_operations(db: Session = Depends(get_db)):
    """List all operations"""
    operations = db.query(Operation).all()
    return operations

@router.get("/{operation_id}", response_model=OperationResponse)
async def get_operation(operation_id: int, db: Session = Depends(get_db)):
    """Get a specific operation by ID"""
    operation = db.query(Operation).filter(Operation.id == operation_id).first()
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    return operation

@router.post("/", response_model=OperationResponse)
async def create_operation(operation: OperationCreate, db: Session = Depends(get_db)):
    """Create a new operation"""
    db_operation = Operation(**operation.dict())
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation

@router.put("/{operation_id}", response_model=OperationResponse)
async def update_operation(operation_id: int, operation: OperationCreate, db: Session = Depends(get_db)):
    """Update an operation"""
    db_operation = db.query(Operation).filter(Operation.id == operation_id).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    for key, value in operation.dict().items():
        setattr(db_operation, key, value)
    
    db_operation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_operation)
    return db_operation

@router.delete("/{operation_id}")
async def delete_operation(operation_id: int, db: Session = Depends(get_db)):
    """Delete an operation"""
    operation = db.query(Operation).filter(Operation.id == operation_id).first()
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    db.delete(operation)
    db.commit()
    return {"message": "Operation deleted successfully"}
