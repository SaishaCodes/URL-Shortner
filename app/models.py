from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from app.database import Base
import datetime

class URL(Base):
    __tablename__ = "urls"
    short_code = Column(String, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Click(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_code = Column(String, ForeignKey("urls.short_code"), index=True)
    clicked_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_agent = Column(String)
    ip_address = Column(String)