from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)

    predicted_class = Column(String(20), nullable=False)   # sharp / used / dulled
    confidence = Column(Float, nullable=False)
    probabilities = Column(JSON, nullable=True)             # {"sharp":0.1,"used":0.2,"dulled":0.7}

    source = Column(String(20), default="video")            # "video" | "manual_upload"
    frame_path = Column(String(255), nullable=True)          # image originale sauvegardée (pour Grad-CAM)
    gradcam_path = Column(String(255), nullable=True)        # heatmap Grad-CAM générée à la demande (cache)
    processing_time_ms = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    machine = relationship("Machine", back_populates="predictions")
    tool = relationship("Tool", back_populates="predictions")
    alert = relationship("Alert", back_populates="prediction", uselist=False)
