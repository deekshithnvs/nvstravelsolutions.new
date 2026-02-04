from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import datetime, timedelta
from models.invoice import Invoice, InvoiceStatus
from fastapi import HTTPException
import hashlib

class ValidationService:
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def validate_invoice(
        db: Session,
        vendor_id: int,
        invoice_no: str,
        invoice_date: datetime,
        amount: float,
        file_hash: str = None
    ):
        """
        Enforce Hard Block validation rules:
        1. Duplicate Number (vendor_id + invoice_no)
        2. Proximity Duplicate (vendor + date + amount within 180 days)
        3. File Hash check
        4. Already Paid check
        5. Age Limit (90 days)
        """
        
        # 5. Age Limit: Invoice date older than 90 days
        ninety_days_ago = datetime.now() - timedelta(days=90)
        if invoice_date < ninety_days_ago:
            raise HTTPException(
                status_code=400, 
                detail=f"HARD BLOCK: Invoice date ({invoice_date.strftime('%Y-%m-%d')}) is older than 90 days limit."
            )

        # 1. Duplicate Number & 4. Already Paid Check
        existing_by_no = db.query(Invoice).filter(
            Invoice.vendor_id == vendor_id,
            Invoice.invoice_no == invoice_no
        ).all()
        
        if existing_by_no:
            # Check if any existing one is marked as PAID
            if any(inv.status == InvoiceStatus.PAID.value for inv in existing_by_no):
                raise HTTPException(
                    status_code=400,
                    detail=f"HARD BLOCK: An invoice with number {invoice_no} marked as PAID already exists."
                )
            # Default duplicate number block
            raise HTTPException(
                status_code=400,
                detail=f"HARD BLOCK: Invoice number {invoice_no} already exists for this vendor."
            )

        # 2. Proximity Duplicate (vendor + date + amount within 180 days)
        one_eighty_days_ago = invoice_date - timedelta(days=180)
        one_eighty_days_after = invoice_date + timedelta(days=180)
        
        proximity_match = db.query(Invoice).filter(
            Invoice.vendor_id == vendor_id,
            Invoice.amount == amount,
            Invoice.invoice_date >= one_eighty_days_ago,
            Invoice.invoice_date <= one_eighty_days_after
        ).first()
        
        if proximity_match:
            raise HTTPException(
                status_code=400,
                detail=f"HARD BLOCK: Potential duplicate found. An invoice with same amount and similar date (within 180 days) exists (Inv: {proximity_match.invoice_no})."
            )

        # 3. File Hash check
        if file_hash:
            duplicate_file = db.query(Invoice).filter(Invoice.file_hash == file_hash).first()
            if duplicate_file:
                raise HTTPException(
                    status_code=400,
                    detail=f"HARD BLOCK: This exact file has already been uploaded (Invoice: {duplicate_file.invoice_no})."
                )

        return True

validation_service = ValidationService()
