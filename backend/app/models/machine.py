import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class MachineStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    maintenance = "maintenance"


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    location = Column(String(120), nullable=True)
    camera_id = Column(String(50), nullable=True)
    status = Column(Enum(MachineStatus), default=MachineStatus.offline, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tools = relationship("Tool", back_populates="machine", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="machine")
    alerts = relationship("Alert", back_populates="machine")
