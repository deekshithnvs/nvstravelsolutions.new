from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base
import enum


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    PENDING_CLARIFICATION = "pending_clarification"
    HOLD = "hold"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"

class DocumentType(str, enum.Enum):
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, index=True, nullable=False)
    document_type = Column(String(20), default=DocumentType.INVOICE, index=True)  # invoice, credit_note, debit_note
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    description = Column(Text)
    category = Column(String(100)) # e.g., 'Travel', 'Software', 'Hardware'
    invoice_date = Column(DateTime)
    file_path = Column(String(500))
    status = Column(String(50), default=InvoiceStatus.PENDING.value, index=True)
    rejection_reason = Column(Text)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approval_comment = Column(Text)
    ocr_confidence = Column(Numeric(5, 2))
    is_handwritten = Column(Integer, default=0) # 0 or 1
    file_hash = Column(String(64), index=True, nullable=True) # SHA-256 hash
    internal_remarks = Column(Text)
    
    # Financial Details
    taxable_value = Column(Numeric(10, 2), default=0)
    non_taxable_value = Column(Numeric(10, 2), default=0)
    discount = Column(Numeric(10, 2), default=0)
    cgst = Column(Numeric(10, 2), default=0)
    sgst = Column(Numeric(10, 2), default=0)
    igst = Column(Numeric(10, 2), default=0)
    
    line_items_json = Column(Text, nullable=True)
    
    # Payment Details
    payment_date = Column(DateTime, nullable=True)
    payment_reference = Column(String(100), nullable=True) # UTR, Cheque No, etc.
    payment_remarks = Column(Text, nullable=True)
    tds_amount = Column(Numeric(10, 2), default=0.0) # TDS Deducted at time of payment
    paid_amount = Column(Numeric(10, 2), nullable=True) # Actual amount paid (after TDS and other deductions)

    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Audit Trail
    audit_logs = relationship("AuditLog", back_populates="invoice")
    
    # Relationships
    vendor = relationship("Vendor", back_populates="invoices")
    approver = relationship("User", back_populates="approved_invoices", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<Invoice {self.invoice_no}>"

# Prevent circular imports but ensure AuditLog is known to the mapper
import models.audit
