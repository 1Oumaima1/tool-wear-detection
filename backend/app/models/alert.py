import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class AlertSeverity(str, enum.Enum):
    warning = "warning"
    critical = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)

    severity = Column(Enum(AlertSeverity), default=AlertSeverity.warning)
    message = Column(String(500), nullable=False)
    confidence = Column(Float, nullable=True)

    email_sent = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    machine = relationship("Machine", back_populates="alerts")
    tool = relationship("Tool", back_populates="alerts")
    prediction = relationship("Prediction", back_populates="alert")
