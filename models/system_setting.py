from sqlalchemy import Column, String, Text
from models.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    key = Column(String(100), primary_key=True, index=True)
    value = Column(Text, nullable=False)
