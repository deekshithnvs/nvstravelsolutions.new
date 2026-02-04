from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from models.database import Base
import enum

class AuditAction(str, enum.Enum):
    UPLOAD = "UPLOAD"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    OVERRIDE = "OVERRIDE"
    PAY = "PAY"
    CANCEL = "CANCEL"
    # Added Actions
    INVOICE_UPLOAD = "INVOICE_UPLOAD"
    REPORT_EXPORT = "REPORT_EXPORT"
    VENDOR_CREATE = "VENDOR_CREATE"
    VENDOR_UPDATE = "VENDOR_UPDATE"
    UPDATE = "UPDATE" # Generic update
    PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
    # New Workflow Actions
    REVIEW = "REVIEW"
    CLARIFY = "CLARIFY"
    HOLD = "HOLD"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True) # Can be null for generic actions, but mostly for invoices
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Null for system actions
    actor_name = Column(String(255)) # Snapshot in case user is deleted
    actor_role = Column(String(50))  # Snapshot
    action = Column(String(50), nullable=False) # Enum as string
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="audit_logs")
    actor = relationship("User")

    def __repr__(self):
        return f"<AuditLog {self.action} on Inv {self.invoice_id} by {self.actor_name}>"
