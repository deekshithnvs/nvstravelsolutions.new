from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional, List
import shutil
import os
import uuid
from datetime import datetime

from core.config import TEMPLATES
from core.dependencies import get_db, require_user, get_current_user, require_admin
from models.invoice import Invoice, InvoiceStatus
from models.vendor import Vendor
from services.workflow import workflow_service
from services.audit import audit_service, AuditAction
from services.notification import notification_service
from services.validation import validation_service

from sqlalchemy.exc import IntegrityError
from core.error_handler import BadRequestError

router = APIRouter()

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def validate_file_extension(filename: str):
    if '.' not in filename:
        raise HTTPException(status_code=400, detail="File has no extension")
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    return ext

@router.get("/invoices", response_class=HTMLResponse)
async def list_invoices(request: Request):
    return TEMPLATES.TemplateResponse("invoices.html", {"request": request})

@router.get("/api/invoices/data")
async def list_my_invoices(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    search: Optional[str] = None,
    vendor_search: Optional[str] = None, # Added vendor search
    sort: Optional[str] = None,
    dir: Optional[str] = "asc",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db), 
    user = Depends(require_user)
):
    # Base Query
    query = db.query(Invoice)

    # Role specific filters
    if user["role"] not in ["admin", "superadmin", "finance"]:
        vendor_id = user.get("vendor_id")
        if not vendor_id:
            raise HTTPException(status_code=403, detail="No vendor linked to account")
        query = query.filter(Invoice.vendor_id == vendor_id)

    # Apply Filters
    if start_date:
        try:
             s_date = datetime.strptime(start_date, "%Y-%m-%d")
             query = query.filter(Invoice.invoice_date >= s_date)
        except: pass
        
    if end_date:
        try:
             e_date = datetime.strptime(end_date, "%Y-%m-%d")
             # Set time to end of day
             e_date = e_date.replace(hour=23, minute=59, second=59)
             query = query.filter(Invoice.invoice_date <= e_date)
        except: pass

    if status and status.strip():
        # Match "Pending Clarification" -> "pending_clarification" etc.
        s_term = status.strip().lower().replace(" ", "_")
        if s_term == "clarification_needed": s_term = InvoiceStatus.PENDING_CLARIFICATION.value
        if s_term == "under_review": s_term = InvoiceStatus.UNDER_REVIEW.value
        
        # Safe string comparison since column is String
        query = query.filter(Invoice.status == s_term)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(Invoice.invoice_no.ilike(term))

    if vendor_search and vendor_search.strip():
        # Join Vendor to filter by company name if not already joined
        if not any(mapper.class_ == Vendor for mapper in query._compile_state()._join_entities):
             query = query.join(Vendor)
        
        term = f"%{vendor_search.strip()}%"
        query = query.filter(Vendor.company_name.ilike(term))

    # Sorting Logic
    if sort:
        sort_column = None
        if sort == "invoice_no": sort_column = Invoice.invoice_no
        elif sort == "date": sort_column = Invoice.invoice_date
        elif sort == "base_amount": sort_column = Invoice.amount
        elif sort == "amount": sort_column = Invoice.amount # Sort by base amount for now as total requires calculation or derived column
        elif sort == "status": sort_column = Invoice.status
        elif sort == "vendor": 
            # Join if not already joined
            if not any(mapper.class_ == Vendor for mapper in query._compile_state()._join_entities):
                 query = query.join(Vendor)
            sort_column = Vendor.company_name
        
        if sort_column:
            if dir == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
             query = query.order_by(Invoice.created_at.desc())
    else:
        query = query.order_by(Invoice.created_at.desc())

    # Pagination Logic
    total_count = query.count()
    offset = (page - 1) * limit
    
    invoices = query.offset(offset).limit(limit).all()
    
    # Calculate Totals for the filtered set (before pagination)
    # Accounting for component taxes if tax_amount is 0
    totals_query = db.query(
        func.sum(Invoice.amount).label("total_amount"),
        func.sum(
            func.coalesce(Invoice.tax_amount, 0) + 
            case(
                (func.coalesce(Invoice.tax_amount, 0) == 0, 
                 func.coalesce(Invoice.cgst, 0) + func.coalesce(Invoice.sgst, 0) + func.coalesce(Invoice.igst, 0)),
                else_=0
            )
        ).label("total_tax"),
        func.sum(func.coalesce(Invoice.igst, 0)).label("total_igst")
    ).filter(Invoice.id.in_(query.with_entities(Invoice.id)))
    
    totals = totals_query.first()
    total_amount = float(totals.total_amount or 0.0)
    total_tax = float(totals.total_tax or 0.0)
    total_igst = float(totals.total_igst or 0.0)

    return {
        "items": [{
            "id": inv.id,
            "invoice_no": inv.invoice_no,
            "vendor_name": inv.vendor.company_name if inv.vendor else "Unknown",
            "date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else "N/A",
            "amount": f"₹{(float(inv.amount or 0) + (float(inv.tax_amount) if inv.tax_amount else (float(inv.cgst or 0) + float(inv.sgst or 0) + float(inv.igst or 0)))):,.2f}", # Total Amount (Base + Tax)
            "base_amount": f"₹{inv.amount:,.2f}", # Base Amount (Stored Amount)
            "taxable_value": f"₹{inv.taxable_value:,.2f}" if inv.taxable_value else "₹0.00",
            "tax": f"₹{(float(inv.tax_amount) if inv.tax_amount else (float(inv.cgst or 0) + float(inv.sgst or 0) + float(inv.igst or 0))):,.2f}",
            "cgst": float(inv.cgst or 0),
            "sgst": float(inv.sgst or 0),
            "igst": float(inv.igst or 0),
            "status": inv.status.replace("_", " ").title() if inv.status else "Pending",
            "file_path": inv.file_path
        } for inv in invoices],
        "total": total_count,
        "total_amount": total_amount,
        "total_tax": total_tax,
        "total_igst": total_igst,
        "page": page,
        "limit": limit
    }


@router.post("/api/invoices/upload-file")
async def upload_file_only(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """Upload file immediately and return file path"""
    # Save File
    file_ext = validate_file_extension(file.filename)
    filename = f"{uuid.uuid4().hex}.{file_ext}"
    upload_dir = "uploads/invoices"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    # Path Traversal Check
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_dir)):
         raise HTTPException(status_code=400, detail="Invalid file path")
    
    content = await file.read()
    file_hash = validation_service.calculate_file_hash(content)
    
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    return {"success": True, "file_path": file_path, "file_hash": file_hash}


@router.post("/api/invoices/submit-metadata")
async def submit_invoice_metadata(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Submit invoice metadata with pre-uploaded file"""
    # Determine Vendor
    vendor_id = user.get("vendor_id")
    manual_vendor_id = payload.get("manual_vendor_id")
    
    # Allow Admin to upload on behalf of vendor
    if user["role"] in ["admin", "superadmin", "finance"] and manual_vendor_id:
        vendor_id = manual_vendor_id
        
    if not vendor_id:
        if user["role"] in ["admin", "superadmin", "finance"]:
            raise HTTPException(status_code=400, detail="Please select a vendor from the dropdown")
        else:
            raise HTTPException(status_code=400, detail="No vendor linked to your account")

    # Get file path from payload
    file_path = payload.get("file_path")
    if not file_path:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Extract metadata
    final_invoice_no = payload.get("manual_invoice_no") or f"INV-{uuid.uuid4().hex[:8].upper()}"
    final_amount = float(payload.get("manual_amount", 0))
    final_tax = float(payload.get("manual_tax", 0))
    final_date_str = payload.get("manual_date")
    
    final_date = datetime.now()
    if final_date_str:
        try:
            final_date = datetime.strptime(final_date_str, "%d-%m-%Y")
        except:
            try:
                final_date = datetime.strptime(final_date_str, "%Y-%m-%d")
            except:
                pass
            
    # Validate
    validation_service.validate_invoice(
        db=db,
        vendor_id=vendor_id,
        invoice_no=final_invoice_no,
        invoice_date=final_date,
        amount=final_amount,
        file_hash=payload.get("file_hash")
    )

    # Validate document type
    valid_doc_types = ["invoice", "credit_note", "debit_note"]
    final_document_type = payload.get("manual_document_type", "invoice")
    if final_document_type not in valid_doc_types:
        final_document_type = "invoice"

    # Create Invoice
    try:
        new_inv = Invoice(
            invoice_no=final_invoice_no,
            document_type=final_document_type,
            vendor_id=vendor_id,
            amount=final_amount,
            tax_amount=final_tax,
            invoice_date=final_date,
            file_path=file_path,
            status=InvoiceStatus.PENDING,
            category=payload.get("manual_category", "General"),
            description=payload.get("manual_description"),
            taxable_value=float(payload.get("manual_taxable_value", 0)),
            non_taxable_value=float(payload.get("manual_non_taxable_value", 0)),
            discount=float(payload.get("manual_discount", 0)),
            cgst=float(payload.get("manual_cgst", 0)),
            sgst=float(payload.get("manual_sgst", 0)),
            igst=float(payload.get("manual_igst", 0)),
            ocr_confidence=0.0,
            is_handwritten=0,
            file_hash=payload.get("file_hash")
        )
        
        db.add(new_inv)
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"success": False, "message": "Invoice number already exists (DB Constraint)"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    # Audit
    audit_service.log_action(db, user["id"], AuditAction.INVOICE_UPLOAD, new_inv.id, f"Uploaded Invoice {final_invoice_no}")
    
    return {"success": True, "message": "Invoice submitted successfully"}


@router.post("/api/invoices/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    manual_invoice_no: Optional[str] = Form(None),
    manual_amount: Optional[float] = Form(None),
    manual_tax: Optional[float] = Form(None),
    manual_taxable_value: Optional[float] = Form(0),
    manual_non_taxable_value: Optional[float] = Form(0),
    manual_discount: Optional[float] = Form(0),
    manual_cgst: Optional[float] = Form(0),
    manual_sgst: Optional[float] = Form(0),
    manual_igst: Optional[float] = Form(0),
    manual_date: Optional[str] = Form(None),
    manual_category: Optional[str] = Form(None),
    manual_description: Optional[str] = Form(None),
    manual_vendor_id: Optional[int] = Form(None), # For Admin Upload
    manual_document_type: Optional[str] = Form("invoice"), # Document Type: invoice, credit_note, debit_note
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # Determine Vendor
    vendor_id = user.get("vendor_id")
    
    # Allow Admin to upload on behalf of vendor
    if user["role"] in ["admin", "superadmin", "finance"] and manual_vendor_id:
        vendor_id = manual_vendor_id
        
    if not vendor_id:
        if user["role"] in ["admin", "superadmin", "finance"]:
            raise HTTPException(status_code=400, detail="Please select a vendor from the dropdown to upload invoice on their behalf")
        else:
            raise HTTPException(status_code=400, detail="No vendor linked to your account. Please contact admin.")


    # Calculate Hash
    content = await file.read()
    file_hash = validation_service.calculate_file_hash(content)
    
    # Save File
    file_ext = validate_file_extension(file.filename)
    filename = f"{uuid.uuid4().hex}.{file_ext}"
    upload_dir = "uploads/invoices"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    
    # Path Traversal Check
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_dir)):
         raise HTTPException(status_code=400, detail="Invalid file path")

    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # Metadata extraction
    final_invoice_no = manual_invoice_no or f"INV-{uuid.uuid4().hex[:8].upper()}"
    final_amount = manual_amount if manual_amount is not None else 0.0
    final_tax = manual_tax if manual_tax is not None else 0.0
    final_date_str = manual_date
    
    final_date = datetime.now()
    if final_date_str:
        try:
            # Try DD-MM-YYYY format first (from frontend)
            final_date = datetime.strptime(final_date_str, "%d-%m-%Y")
        except:
            try:
                # Fallback to YYYY-MM-DD format
                final_date = datetime.strptime(final_date_str, "%Y-%m-%d")
            except:
                pass

    # Validation
    validation_service.validate_invoice(
        db=db,
        vendor_id=vendor_id,
        invoice_no=final_invoice_no,
        invoice_date=final_date,
        amount=final_amount,
        file_hash=file_hash
    )

    # Validate document type
    valid_doc_types = ["invoice", "credit_note", "debit_note"]
    final_document_type = manual_document_type if manual_document_type in valid_doc_types else "invoice"

    # Create Invoice
    new_inv = Invoice(
        invoice_no=final_invoice_no,
        document_type=final_document_type,
        vendor_id=vendor_id,
        amount=final_amount,
        tax_amount=final_tax,
        invoice_date=final_date,
        file_path=file_path,
        status=InvoiceStatus.PENDING,
        category=manual_category or "General",
        description=manual_description,
        taxable_value=manual_taxable_value or 0.0,
        non_taxable_value=manual_non_taxable_value or 0.0,
        discount=manual_discount or 0.0,
        cgst=manual_cgst or 0.0,
        sgst=manual_sgst or 0.0,
        igst=manual_igst or 0.0,
        ocr_confidence=0.0, # OCR Removed
        is_handwritten=0,
        file_hash=file_hash
    )
    
    # Workflow is now flat
    
    try:
        db.add(new_inv)
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"success": False, "message": "Invoice number already exists"}
    
    # Audit
    audit_service.log_action(db, user["id"], AuditAction.INVOICE_UPLOAD, new_inv.id, f"Uploaded Invoice {final_invoice_no}")
    
    return {
        "success": True, 
        "message": "Invoice uploaded successfully",
        "mismatch": False 
    }

@router.post("/api/invoices/recategorise")
async def recategorise_invoice(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user = Depends(require_admin) # Only admins/superadmins
):
    invoice_no = payload.get("invoice_no")
    new_category = payload.get("category")
    
    if not invoice_no or not new_category:
        raise HTTPException(status_code=400, detail="Missing required fields")
        
    invoice = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    old_category = invoice.category
    invoice.category = new_category
    
    # Audit
    audit_service.log_action(db, user["id"], AuditAction.UPDATE, f"Changed category from {old_category} to {new_category}", invoice.id)
    
    db.commit()
    return {"success": True, "message": f"Category updated to {new_category}"}

@router.post("/api/invoices/update-status")
async def update_invoice_status(
    payload: dict = Body(...), 
    db: Session = Depends(get_db), 
    admin = Depends(require_admin)
):
    invoice_no = payload.get("invoice_no")
    status = payload.get("status") # 'approved' or 'rejected'
    reason = payload.get("reason")
    
    inv = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()
    if not inv: raise HTTPException(status_code=404)
    
    if status == "rejected":
        inv.status = InvoiceStatus.REJECTED
        inv.rejection_reason = reason
        audit_action = AuditAction.REJECT
    elif status == "approved":
        inv.status = InvoiceStatus.APPROVED
        audit_action = AuditAction.APPROVE
    elif status == "under_review":
        inv.status = InvoiceStatus.UNDER_REVIEW
        audit_action = AuditAction.REVIEW
    elif status == "pending_clarification":
        inv.status = InvoiceStatus.PENDING_CLARIFICATION
        audit_action = AuditAction.CLARIFY
    elif status == "hold":
        inv.status = InvoiceStatus.HOLD
        audit_action = AuditAction.HOLD
    else:
        raise HTTPException(status_code=400, detail="Invalid status")

    # Audit Action
    audit_service.log_action(db, admin["id"], audit_action, inv.id, f"Invoice {status} by admin. Comment: {reason or 'N/A'}")

    db.commit()
    return {"success": True}

@router.post("/api/invoices/update-payment")
async def update_payment(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user = Depends(require_admin)
):
    invoice_no = payload.get("invoice_no")
    payment_date = payload.get("payment_date")
    payment_reference = payload.get("payment_reference")
    payment_remarks = payload.get("payment_remarks")
    tds_amount = payload.get("tds_amount")
    paid_amount = payload.get("paid_amount")
    
    if not invoice_no or not payment_reference:
        raise HTTPException(status_code=400, detail="Invoice No and Payment Reference (UTR/Cheque) are required")
        
    invoice = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # Update Fields
    if payment_date:
        from datetime import datetime
        try:
            # Assume YYYY-MM-DD
            invoice.payment_date = datetime.strptime(payment_date, "%Y-%m-%d")
        except ValueError:
             # Try other format or ignore if failed, but for now strict
             pass
             
    invoice.payment_reference = payment_reference
    invoice.payment_remarks = payment_remarks
    if tds_amount is not None:
        try:
            invoice.tds_amount = float(tds_amount)
        except ValueError:
            invoice.tds_amount = 0.0

    if paid_amount is not None:
        try:
            invoice.paid_amount = float(paid_amount)
        except ValueError:
            invoice.paid_amount = 0.0
            
    invoice.status = InvoiceStatus.PAID
    
    # Audit
    audit_msg = f"Payment Processed: {payment_reference}"
    if tds_amount:
        audit_msg += f" (TDS: {tds_amount})"
    if paid_amount:
        audit_msg += f" (Paid: {paid_amount})"
    audit_service.log_action(db, user["id"], AuditAction.PAYMENT_PROCESSED, invoice.id, audit_msg)
    
    db.commit()
    
    return {"success": True, "message": "Payment details updated and invoice marked as PAID",
        "mismatch": False 
    }

@router.get("/api/invoices/detail")
async def get_invoice_detail(invoice_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # Access Control
    if user["role"] == "vendor" and inv.vendor_id != user["vendor_id"]:
        raise HTTPException(status_code=403, detail="Access Denied")

    vendor = db.query(Vendor).filter(Vendor.id == inv.vendor_id).first()
    
    # Return calculated tax if tax_amount is 0
    tax_amount = inv.tax_amount
    if not tax_amount or float(tax_amount) == 0:
        tax_amount = float(inv.cgst or 0) + float(inv.sgst or 0) + float(inv.igst or 0)

    base_val = float(inv.amount or 0)
    tax_val = float(tax_amount or 0)
    total_val = base_val + tax_val

    return {
        "id": inv.id,
        "invoice_no": inv.invoice_no,
        "vendor_name": vendor.company_name if vendor else "Unknown",
        "amount": total_val,          # Total (Base + Tax)
        "base_amount": base_val,      # Base (Stored Amount)
        "tax_amount": tax_val,
        "taxable_value": float(inv.taxable_value or 0.0),
        "non_taxable_value": inv.non_taxable_value or 0.0,
        "discount": inv.discount or 0.0,
        "cgst": inv.cgst or 0.0,
        "sgst": inv.sgst or 0.0,
        "igst": inv.igst or 0.0,
        "date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else "N/A",
        "status": inv.status,
        "ocr_confidence": inv.ocr_confidence or 0.0,
        "is_handwritten": bool(inv.is_handwritten),
        "file_path": inv.file_path,
        "line_items": [], # Mock for now
        "vendor_tds_applicable": vendor.tds_applicable if vendor else False,
        "vendor_tds_rate": vendor.tds_rate if vendor else 0.0,
        # Payment Info
        "payment_date": inv.payment_date.strftime("%Y-%m-%d") if inv.payment_date else None,
        "payment_reference": inv.payment_reference,
        "payment_remarks": inv.payment_remarks,
        "paid_amount": inv.paid_amount,
        "tds_deducted": inv.tds_amount
    }

@router.get("/api/invoices/view-original")
async def view_original_file(invoice_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv: raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Access Control
    if user["role"] == "vendor" and inv.vendor_id != user["vendor_id"]:
        raise HTTPException(status_code=403, detail="Access Denied")

    if not os.path.exists(inv.file_path):
         raise HTTPException(status_code=404, detail="File not found on server")
         
    return FileResponse(inv.file_path)
