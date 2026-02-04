from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import os

from core.dependencies import get_db, require_user, get_current_user
from models.invoice import Invoice, InvoiceStatus
from models.vendor import Vendor
from services.reporting import reporting_service
from services.audit import audit_service, AuditAction

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/invoices-csv")
async def export_invoices_csv(
    db: Session = Depends(get_db),
    user = Depends(require_user)
):
    """Generate CSV report of invoices."""
    # Filter by vendor if user is a vendor
    query = db.query(Invoice)
    if user["role"] == "vendor":
        vendor_id = user.get("vendor_id")
        if not vendor_id:
            raise HTTPException(status_code=403, detail="No vendor linked to account")
        query = query.filter(Invoice.vendor_id == vendor_id)
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    # Format data for reporting service
    report_data = []
    for inv in invoices:
        report_data.append({
            "payment_reference": inv.payment_reference or "N/A",
            "invoice_no": inv.invoice_no,
            "date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else "N/A",
            "vendor_name": inv.vendor.company_name if inv.vendor else "Unknown",
            "amount": float(inv.amount or 0),
            "tax_amount": float(inv.tax_amount or 0),
            "status": inv.status.value.replace("_", " ").title() if hasattr(inv.status, 'value') else str(inv.status).replace("_", " ").title(),
            "is_handwritten": "Yes" if inv.is_handwritten else "No"
        })
    
    csv_content = reporting_service.generate_invoice_csv(report_data)
    
    # Log audit
    audit_service.log_action(db, user["id"], AuditAction.REPORT_EXPORT, f"Exported Invoices CSV Report ({len(report_data)} records)")
    
    from fastapi.responses import Response
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices_report.csv"}
    )
