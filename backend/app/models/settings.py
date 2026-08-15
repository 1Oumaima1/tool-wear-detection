from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base


class PlatformSettings(Base):
    """
    Table à une seule ligne (id=1) contenant la configuration modifiable
    depuis la page Settings du dashboard, sans redéploiement.
    """
    __tablename__ = "platform_settings"

    id = Column(Integer, primary_key=True, default=1)

    frame_interval_seconds = Column(Float, default=2.0)
    confidence_threshold = Column(Float, default=0.75)
    consecutive_detections_required = Column(Integer, default=3)

    smtp_host = Column(String(120), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String(120), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    alert_email_to = Column(String(255), nullable=True)

    default_machine_name = Column(String(120), nullable=True)
    default_camera_id = Column(String(50), nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
