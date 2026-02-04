from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime

from core.dependencies import get_db, require_admin, get_current_user
from models.tax_document import VendorTaxDocument, TaxQuarter
from models.vendor import Vendor
from services.audit import audit_service, AuditAction

router = APIRouter(prefix="/api/tax-docs", tags=["Tax Documents"])

UPLOAD_DIR = "uploads/tax_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_tax_document(
    file: UploadFile = File(...),
    vendor_id: int = Form(...),
    financial_year: str = Form(...), # e.g. "2024-2025"
    quarter: str = Form(...), # Q1, Q2, Q3, Q4
    document_type: str = Form("Form 16A"), # Form 16, Form 16A
    remarks: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    # Validate File
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate Vendor
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Security: Validate inputs for path traversal
    safe_year = "".join(x for x in financial_year if x.isalnum() or x in "-")
    safe_quarter = "".join(x for x in quarter if x.isalnum())
    
    if safe_year != financial_year or safe_quarter != quarter:
         raise HTTPException(status_code=400, detail="Invalid characters in Year or Quarter")

    # Save File
    filename = f"{vendor_id}_{safe_year}_{safe_quarter}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Double check path traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIR)):
         raise HTTPException(status_code=400, detail="Invalid file path")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # check for existing to avoid duplicates? Or allow overwrite/multiple?
    # Let's allow multiple for now, or maybe replace? 
    # Logic: If same vendor, year, quarter exists, maybe warn? For now, just add new.

    new_doc = VendorTaxDocument(
        vendor_id=vendor_id,
        file_path=file_path,
        financial_year=financial_year,
        quarter=quarter,
        document_type=document_type,
        remarks=remarks,
        uploaded_by=admin["id"]
    )
    
    db.add(new_doc)
    db.commit()
    
    # Audit
    audit_service.log_action(db, admin["id"], AuditAction.UPDATE, new_doc.id, f"Uploaded Form 16A for Vendor {vendor.company_name} ({financial_year} {quarter})")
    
    return {"success": True, "message": "Form 16A uploaded successfully"}

@router.get("/list")
async def list_tax_documents(
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # Requirement: TDS & Form 16 should not be visible to vendor
    if user["role"] == "vendor":
        return []

    query = db.query(VendorTaxDocument)
    
    # Implementation: Remove TDS certificates if no new file has been uploaded within 30 days
    # (Logic: Only show documents uploaded in the last 30 days)
    import datetime as dt
    thirty_days_ago = dt.datetime.now() - dt.timedelta(days=30)
    query = query.filter(VendorTaxDocument.created_at >= thirty_days_ago)

    if vendor_id:
        # Admin can filter by vendor
        query = query.filter(VendorTaxDocument.vendor_id == vendor_id)
        
    docs = query.order_by(VendorTaxDocument.created_at.desc()).all()
    
    return [{
        "id": doc.id,
        "vendor_name": doc.vendor.company_name,
        "financial_year": doc.financial_year,
        "quarter": doc.quarter,
        "document_type": doc.document_type,
        "remarks": doc.remarks,
        "uploaded_at": doc.created_at.strftime("%Y-%m-%d"),
        "filename": os.path.basename(doc.file_path)
    } for doc in docs]

@router.get("/download/{doc_id}")
async def download_tax_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    doc = db.query(VendorTaxDocument).filter(VendorTaxDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Access Control
    if user["role"] == "vendor" and doc.vendor_id != user["vendor_id"]:
        raise HTTPException(status_code=403, detail="Access Denied")
        
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    return FileResponse(
        doc.file_path, 
        media_type="application/pdf", 
        filename=f"Form16A_{doc.financial_year}_{doc.quarter}.pdf"
    )
