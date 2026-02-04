from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from core.config import TEMPLATES
from core.dependencies import get_current_user, get_db

router = APIRouter()

@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(content="", media_type="image/x-icon")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return TEMPLATES.TemplateResponse("index.html", {"request": request})


@router.post("/api/ai/chat")
async def ai_chat(request: Request, user = Depends(get_current_user)):
    """AI Chat helper - requires authentication."""
    data = await request.json()
    user_message = data.get("message", "").lower()
    
    # Simple Mock AI Logic
    if "invoice" in user_message:
        response = "To upload an invoice, click the 'Upload Invoice' button on your dashboard. I can handle PDF and clear images."
    elif "gst" in user_message:
        response = "I automatically extract GSTINs. Make sure yours is clearly visible in the top header of the bill."
    elif "status" in user_message:
        response = "You can track your invoice status in the 'Recent Invoices' section. 'Under Review' means finance is checking it."
    else:
        response = "I'm learning about NVS Travels! I can help with invoice uploads, status tracking, and portal navigation."
        
    return {"response": response}
    
@router.get("/api/chat/history")
async def get_chat_history(request: Request, receiver_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    from models.message import Message
    from models.user import User
    from sqlalchemy import or_, and_
    
    current_user_id = user["id"]
    
    # Access Control: Vendors can only chat with Admins/Finance
    if user["role"] == "vendor":
        receiver = db.query(User).filter(User.id == receiver_id).first()
        if not receiver or receiver.role not in ["admin", "superadmin", "finance"]:
            raise HTTPException(status_code=403, detail="Vendors can only chat with administrative staff.")
    
    # Fetch messages between current user and receiver
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user_id, Message.receiver_id == receiver_id),
            and_(Message.sender_id == receiver_id, Message.receiver_id == current_user_id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    return [{
        "id": m.id,
        "content": m.content,
        "sender_id": m.sender_id,
        "receiver_id": m.receiver_id,
        "timestamp": m.created_at.isoformat(),
        "is_me": m.sender_id == current_user_id
    } for m in messages]

@router.post("/api/chat/send")
async def send_chat_message(request: Request, payload: dict = Body(...), db: Session = Depends(get_db), user = Depends(get_current_user)):
    from models.message import Message
    
    receiver_id = payload.get("receiver_id")
    content = payload.get("content")
    
    if not content or not receiver_id:
        raise HTTPException(status_code=400, detail="Missing receiver_id or content")
    
    # Access Control: Vendors can only chat with Admins/Finance
    if user["role"] == "vendor":
        from models.user import User
        receiver = db.query(User).filter(User.id == receiver_id).first()
        if not receiver or receiver.role not in ["admin", "superadmin", "finance"]:
            raise HTTPException(status_code=403, detail="Vendors can only chat with administrative staff.")
        
    new_msg = Message(
        sender_id=user["id"],
        receiver_id=receiver_id,
        content=content
    )
    db.add(new_msg)
    db.commit()
    
    return {"success": True, "message_id": new_msg.id}
