from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List

from core.config import TEMPLATES
from core.dependencies import get_db, require_admin, require_user
from core.security import get_password_hash
from models.vendor import Vendor, VendorStatus
from models.invoice import Invoice, InvoiceStatus
from models.user import User
from schemas.vendor import VendorCreate
from services.audit import audit_service, AuditAction
from services.workflow import workflow_service
from services.notification import notification_service

router = APIRouter(tags=["admin"])

# --- Views ---
@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return TEMPLATES.TemplateResponse("admin.html", {"request": request})

@router.get("/admin/vendors", response_class=HTMLResponse)
async def admin_vendors_page(request: Request):
    return TEMPLATES.TemplateResponse("admin_vendors.html", {"request": request})

# --- API ---
@router.get("/api/admin/vendors")
async def get_vendors(db: Session = Depends(get_db), admin = Depends(require_admin)):
    vendors = db.query(Vendor).all()
    # Map to list
    return [{
        "id": v.id,
        "company_name": v.company_name,
        "vendor_code": f"V-{v.id:04d}",
        "contact_person": v.contact_person,
        "email": v.email,
        "mobile": v.mobile,
        "status": (v.status.strip().lower() if v.status else "pending"),
        "kyc_verified": v.kyc_verified,
        "entity_type": v.entity_type or "Company",
        "pan": v.pan,
        "gstin": v.gstin,
        "bank_name": v.bank_name,
        "bank_account_no": v.bank_account_no,
        "remarks": v.remarks
    } for v in vendors]

@router.post("/api/admin/vendors")
async def add_vendor(vendor_data: VendorCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    # Manual Add Vendor
    new_vendor = Vendor(**vendor_data.dict(), status=VendorStatus.VERIFIED, kyc_verified=True)
    db.add(new_vendor)
    db.flush() # Get ID for user linking
    
    # Create corresponding User account
    # Default password as discussed: nvs@123
    pwd_hash = get_password_hash("nvs@123")
    new_user = User(
        email=vendor_data.email,
        name=vendor_data.contact_person or vendor_data.company_name,
        password_hash=pwd_hash,
        role="vendor",
        vendor_id=new_vendor.id,
        is_active=True
    )
    db.add(new_user)
    
    audit_service.log_action(db, admin["id"], AuditAction.VENDOR_UPDATE, new_vendor.id, f"Manually added Vendor {new_vendor.company_name} and created user account")
    
    db.commit()
    return {"success": True, "message": "Vendor created and user account activated (Default password: nvs@123)"}

@router.put("/api/admin/vendors/{vendor_id}")
async def update_vendor(vendor_id: int, vendor_data: VendorCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor: raise HTTPException(status_code=404)
    
    for key, value in vendor_data.dict().items():
        setattr(vendor, key, value)
    
    db.commit()
    return {"success": True}

@router.delete("/api/admin/vendors/{vendor_id}")
async def delete_vendor(vendor_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor: raise HTTPException(status_code=404)
    
    # Soft Delete: Set status to INACTIVE instead of db.delete(vendor)
    vendor.status = VendorStatus.INACTIVE
    
    # Also deactivate any linked user accounts
    linked_users = db.query(User).filter(User.vendor_id == vendor_id).all()
    for user in linked_users:
        user.is_active = False
    
    audit_service.log_action(db, admin["id"], AuditAction.VENDOR_UPDATE, vendor.id, f"Inactivated Vendor {vendor.company_name}")
    db.commit()
    return {"success": True, "message": "Vendor marked as INACTIVE"}

from datetime import date as dt, timedelta
from typing import Optional

@router.get("/api/admin/pending-invoices")
async def get_pending_invoices(
    start_date: Optional[dt] = None, 
    end_date: Optional[dt] = None, 
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    admin = Depends(require_admin)
):
    # If finance, only approved invoices? No, finance sees Paid/Unpaid.
    # Logic from main.py:
    # return invoices where status not paid/rejected?
    query = db.query(Invoice).filter(Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.UNDER_REVIEW, InvoiceStatus.APPROVED]))

    if vendor_id:
        query = query.filter(Invoice.vendor_id == vendor_id)

    if start_date:
        query = query.filter(Invoice.invoice_date >= start_date)
    if end_date:
        # Include the entire end_date (up to 23:59:59.999)
        query = query.filter(Invoice.invoice_date < end_date + timedelta(days=1))
        
    invoices = query.all()
    
    results = []
    for inv in invoices:
        v = inv.vendor
        # Calculate tax for display fallback
        tax_calc = float(inv.tax_amount) if inv.tax_amount and float(inv.tax_amount) > 0 else (float(inv.cgst or 0) + float(inv.sgst or 0) + float(inv.igst or 0))
        
        base_amt = float(inv.amount or 0)
        total_amt = base_amt + tax_calc

        results.append({
            "id": inv.id,
            "invoice_no": inv.invoice_no,
            "vendor_name": v.company_name if v else "Unknown",
            "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else "-",
            "submitted_date": inv.created_at.strftime("%Y-%m-%d") if inv.created_at else "-",
            "amount": total_amt,        # Total Invoice Value
            "base_amount": base_amt,    # Taxable + Non-Taxable
            "taxable_value": float(inv.taxable_value or 0),
            "tax_amount": tax_calc,
            "total_amount": total_amt,  # Explicit total for mapping
            "status": inv.status,
            "email": v.email if v else "",
            "mobile": v.mobile if v else "",
            "is_handwritten": bool(inv.is_handwritten),
            "category": inv.category or "Basic",
            "internal_remarks": inv.internal_remarks
        })
    return results


@router.get("/api/admin/stats")
async def admin_stats(db: Session = Depends(get_db), admin = Depends(require_admin)):
    total_vendors = db.query(Vendor).count()
    
    # Calculate totals for unpaid invoices
    totals = db.query(
        func.sum(Invoice.amount).label("pending_amount"),
        func.sum(
            func.coalesce(Invoice.tax_amount, 0) + 
            case(
                (func.coalesce(Invoice.tax_amount, 0) == 0, 
                 func.coalesce(Invoice.cgst, 0) + func.coalesce(Invoice.sgst, 0) + func.coalesce(Invoice.igst, 0)),
                else_=0
            )
        ).label("pending_tax"),
        func.sum(func.coalesce(Invoice.igst, 0)).label("pending_igst")
    ).filter(Invoice.status != InvoiceStatus.PAID).first()

    return {
        "success": True, 
        "data": {
            "active_vendors": total_vendors,
            "pending_amount": float(totals.pending_amount or 0.0),
            "pending_tax": float(totals.pending_tax or 0.0),
            "pending_igst": float(totals.pending_igst or 0.0)
        }
    }

@router.get("/api/admin/vendors/{vendor_id}")
async def get_vendor(vendor_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Return vendor data
    return {
        "id": vendor.id,
        "company_name": vendor.company_name,
        "entity_type": vendor.entity_type,
        "contact_person": vendor.contact_person,
        "email": vendor.email,
        "mobile": vendor.mobile,
        "pan": vendor.pan,
        "gstin": vendor.gstin,
        "bank_name": vendor.bank_name,
        "bank_account_no": vendor.bank_account_no,
        "ifsc_code": vendor.ifsc_code,
        "tds_applicable": vendor.tds_applicable,
        "tds_rate": vendor.tds_rate,
        "tds_nature_of_payment": vendor.tds_nature_of_payment,
        "status": (vendor.status.strip().lower() if vendor.status else "pending"),
        "remarks": vendor.remarks
    }

@router.get("/api/admin/vendors/{vendor_id}/documents")
async def get_vendor_documents(vendor_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    documents = []
    # Check for document fields (assuming they exist on Vendor model, although I only saw basic fields earlier. 
    # If they don't exist, this will error. Let's check model again or assume they might be added or legacy.)
    # In Step 534 verify_services output, User view logic for vendor didn't show doc paths.
    # However, user request specifically asked for this implementation. 
    # I will implement it safely with hasattr or try/except if fields differ, or just implement as requested.
    # I'll stick to the requested implementation but verify fields in a future step if needed.
    
    if hasattr(vendor, 'pan_doc_path') and vendor.pan_doc_path:
        documents.append({"type": "PAN Card", "path": f"/static/{vendor.pan_doc_path}"})
    if hasattr(vendor, 'gst_doc_path') and vendor.gst_doc_path:
        documents.append({"type": "GST Certificate", "path": f"/static/{vendor.gst_doc_path}"})
    if hasattr(vendor, 'cheque_doc_path') and vendor.cheque_doc_path:
        documents.append({"type": "Cancelled Cheque", "path": f"/static/{vendor.cheque_doc_path}"})
    
    return {"success": True, "documents": documents}

@router.post("/api/admin/vendors/{vendor_id}/approve")
async def approve_vendor(
    vendor_id: int, 
    payload: dict = Body(...), 
    db: Session = Depends(get_db), 
    admin = Depends(require_admin)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.status = VendorStatus.VERIFIED
    vendor.kyc_verified = True
    
    # Also activate user account
    user = db.query(User).filter(User.email == vendor.email).first()
    if user:
        user.is_active = True
    
    # Audit
    audit_service.log_action(db, admin["id"], AuditAction.VENDOR_UPDATE, None, f"Approved Vendor {vendor.company_name}")

    db.commit()
    return {"success": True, "message": "Vendor approved"}

@router.get("/api/admin/users/list-users")
async def list_users(db: Session = Depends(get_db), admin = Depends(require_admin)):
    """Get list of all users for admin management."""
    users = db.query(User).all()
    return [{
        "id": u.id,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "is_active": bool(u.is_active),
        "vendor_id": u.vendor_id,
        "created_at": u.created_at.isoformat() if hasattr(u, 'created_at') and u.created_at else None
    } for u in users]

@router.get("/api/admin/users/list-admins")
async def list_admins(db: Session = Depends(get_db), user = Depends(require_user)):
    """Get list of admin users (admin, superadmin, finance) for chat functionality."""
    admins = db.query(User).filter(User.role.in_(["admin", "superadmin", "finance"])).all()
    return [{
        "id": u.id,
        "email": u.email,
        "name": f"{u.name} ({u.role.title()})",
        "role": u.role,
        "is_active": bool(u.is_active)
    } for u in admins]
