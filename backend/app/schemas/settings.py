from datetime import datetime
from pydantic import BaseModel


class SettingsRead(BaseModel):
    frame_interval_seconds: float
    confidence_threshold: float
    consecutive_detections_required: int
    smtp_host: str | None
    smtp_port: int | None
    smtp_user: str | None
    alert_email_to: str | None
    default_machine_name: str | None
    default_camera_id: str | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    frame_interval_seconds: float | None = None
    confidence_threshold: float | None = None
    consecutive_detections_required: int | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    alert_email_to: str | None = None
    default_machine_name: str | None = None
    default_camera_id: str | None = None
