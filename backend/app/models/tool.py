from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    tool_identifier = Column(String(50), nullable=False)  # e.g. "T1R2B1"
    tool_type = Column(String(80), nullable=True)         # e.g. "End Mill", "Drill Bit"
    installed_at = Column(DateTime, default=datetime.utcnow)
    last_status = Column(String(20), nullable=True)       # last known: sharp/used/dulled
    last_inspection_at = Column(DateTime, nullable=True)

    machine = relationship("Machine", back_populates="tools")
    predictions = relationship("Prediction", back_populates="tool")
    alerts = relationship("Alert", back_populates="tool")
