from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base
from datetime import datetime

class Session(Base):
    """Database model for persistent sessions."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vendor_id = Column(Integer, nullable=True)  # Populated for vendor role users
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to User
    user = relationship("User", backref="sessions")
