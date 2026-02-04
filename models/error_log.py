from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from models.database import Base

class ErrorLog(Base):
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    endpoint = Column(String(500))
    method = Column(String(10))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # AI Analysis Fields
    ai_suggestion = Column(Text) # Suggested fix from LLM
    is_resolved = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=func.now(), index=True)

    def __repr__(self):
        return f"<ErrorLog {self.id}: {self.error_message[:50]}...>"
