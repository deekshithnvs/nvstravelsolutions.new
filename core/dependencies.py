from fastapi import Request, HTTPException, Depends
from models.database import get_db
from services.auth import auth_service

async def get_current_user(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
        
    session = auth_service.validate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or Expired Session")
    return session

async def require_admin(user = Depends(get_current_user)):
    """Only allow Admin role."""
    if user["role"] not in ["admin", "superadmin", "finance"]:
        # We still allow these role strings if they exist in DB for now, 
        # but logic is consolidated.
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    return user

async def require_user(user = Depends(get_current_user)):
    """Require any authenticated user."""
    return user
