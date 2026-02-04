from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from models.database import Base
import enum

class VendorStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile = Column(String(15))
    pan = Column(String(10))
    gstin = Column(String(15))
    
    # Bank Details
    bank_account_no = Column(String(50))
    bank_name = Column(String(255))
    ifsc_code = Column(String(20))
    account_holder_name = Column(String(255))
    
    address = Column(Text)
    entity_type = Column(String(50), default="Company") # Added Entity Type
    status = Column(String(50), default=VendorStatus.PENDING, index=True)
    kyc_verified = Column(Boolean, default=False)
    # TDS Compliance
    tds_applicable = Column(Boolean, default=False) # True for Yes, False for No
    tds_rate = Column(Numeric(10, 2), default=0.00)      # e.g., 2.0, 10.0
    tds_nature_of_payment = Column(String(255)) # e.g., 194C, 194J
    # Document Paths
    pan_doc_path = Column(String(500))
    gst_doc_path = Column(String(500))
    msme_doc_path = Column(String(500))
    coi_doc_path = Column(String(500))
    cheque_doc_path = Column(String(500))
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    remarks = Column(Text)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="vendor")
    users = relationship("User", back_populates="vendor")
    
    def __repr__(self):
        return f"<Vendor {self.company_name}>"
