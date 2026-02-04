from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from models.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VENDOR = "vendor"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.VENDOR)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    
    # Relationships
    approved_invoices = relationship("Invoice", back_populates="approver")
    vendor = relationship("Vendor", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.email}>"
