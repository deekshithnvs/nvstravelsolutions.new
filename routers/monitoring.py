from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.dependencies import get_db, require_admin
from models.error_log import ErrorLog

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

@router.get("/errors")
async def get_error_logs(db: Session = Depends(get_db), admin = Depends(require_admin)):
    """Retrieve the latest error logs for admin oversight."""
    return db.query(ErrorLog).order_by(ErrorLog.timestamp.desc()).limit(50).all()

@router.post("/analyze/{error_id}")
async def analyze_error(error_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
    """
    Trigger AI analysis for a specific error.
    In a real-world scenario, this would call an LLM API.
    For this 'Ultra-Clean' setup, we simulate the AI diagnostic.
    """
    error_log = db.query(ErrorLog).filter(ErrorLog.id == error_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
        
    # Simulated AI Diagnostic Logic
    stack = error_log.stack_trace or ""
    suggestion = "Examine the function logic for null pointers or missing DB attributes."
    
    if "KeyError" in error_log.error_message:
        suggestion = "AI suggesting: Check if the required key exists in the payload or the database model has been updated."
    elif "db" in stack.lower():
        suggestion = "AI suggesting: Database connection issue or query syntax error detected. Check SQL logs."
    
    error_log.ai_suggestion = suggestion
    db.commit()
    
    return {"id": error_id, "suggestion": suggestion}

@router.post("/resolve/{error_id}")
async def resolve_error(error_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
    """Mark an error as resolved."""
    error_log = db.query(ErrorLog).filter(ErrorLog.id == error_id).first()
    if not error_log:
        raise HTTPException(status_code=404)
        
    error_log.is_resolved = True
    db.commit()
    return {"success": True}
