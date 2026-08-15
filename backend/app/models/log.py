import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.database import Base


class LogLevel(str, enum.Enum):
    info = "info"
    warning = "warning"
    error = "error"


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(Enum(LogLevel), default=LogLevel.info)
    source = Column(String(80), nullable=True)   # e.g. "inference_service", "email_service"
    message = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
