from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from core.dependencies import get_db, require_admin
# SystemSetting might be needed for other things later, but theme is gone.

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/status")
async def get_status():
    return {"status": "ok", "message": "Settings API is active"}
