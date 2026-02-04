from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException, Body
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import shutil
import os
from datetime import datetime

from core.config import TEMPLATES
from core.dependencies import get_db, require_admin, get_current_user, require_user
from models.vendor import Vendor, VendorStatus
from models.user import User
from services.audit import audit_service, AuditAction

router = APIRouter()

# --- API Endpoints ---

@router.get("/api/vendor/profile")
async def get_vendor_profile(db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user["role"] != "vendor" or not user.get("vendor_id"):
        raise HTTPException(status_code=400, detail="User is not linked to a vendor profile")
        
    vendor = db.query(Vendor).filter(Vendor.id == user["vendor_id"]).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
        
    return {
        "id": vendor.id,
        "company_name": vendor.company_name,
        "email": vendor.email,
        "mobile": vendor.mobile,
        "pan": vendor.pan,
        "gstin": vendor.gstin,
        "entity_type": vendor.entity_type,
        "kyc_verified": vendor.kyc_verified,
        "bank_account_no": vendor.bank_account_no,
        "bank_name": vendor.bank_name,
        "ifsc_code": vendor.ifsc_code,
        "status": vendor.status
    }

@router.get("/api/vendor/stats")
async def get_vendor_stats(db: Session = Depends(get_db), user = Depends(require_user)):
    """Get statistics for dashboard. Admins see global stats, vendors see their own."""
    from models.invoice import Invoice, InvoiceStatus
    from sqlalchemy import func
    
    vendor_id = user.get("vendor_id")
    is_admin = user.get("role") in ["admin", "superadmin", "finance"]
    
    query = db.query(Invoice)
    if not is_admin:
        if not vendor_id:
             raise HTTPException(status_code=400, detail="No vendor linked to account")
        query = query.filter(Invoice.vendor_id == vendor_id)
    
    total_invoices = query.count()
    pending = query.filter(Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.UNDER_REVIEW])).count()
    paid_amount = query.filter(Invoice.status == InvoiceStatus.PAID).with_entities(func.sum(Invoice.amount)).scalar() or 0.0
    
    return {
        "success": True,
        "data": {
            "total_invoices": total_invoices,
            "pending_count": pending,
            "paid_amount": paid_amount
        }
    }
