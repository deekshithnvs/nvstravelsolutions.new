from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base
import enum

class TaxQuarter(str, enum.Enum):
    Q1 = "Q1" # Apr-Jun
    Q2 = "Q2" # Jul-Sep
    Q3 = "Q3" # Oct-Dec
    Q4 = "Q4" # Jan-Mar

class VendorTaxDocument(Base):
    __tablename__ = "vendor_tax_documents"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    financial_year = Column(String(20), nullable=False) # e.g., "2025-2026"
    quarter = Column(Enum(TaxQuarter), nullable=False)
    document_type = Column(String(50), default="Form 16A") # Form 16, Form 16A
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=func.now())
    remarks = Column(Text)
    
    # Relationships
    vendor = relationship("Vendor", backref="tax_documents")
    uploader = relationship("User")

    def __repr__(self):
        return f"<TaxDoc {self.financial_year} {self.quarter} - Vendor {self.vendor_id}>"
