from datetime import datetime
from pydantic import BaseModel
from app.models.alert import AlertSeverity


class PredictionRead(BaseModel):
    id: int
    machine_id: int
    tool_id: int
    predicted_class: str
    confidence: float
    probabilities: dict | None
    source: str
    frame_path: str | None
    gradcam_path: str | None
    processing_time_ms: float | None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRead(BaseModel):
    id: int
    machine_id: int
    tool_id: int
    prediction_id: int | None
    severity: AlertSeverity
    message: str
    confidence: float | None
    email_sent: bool
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ManualPredictionResult(BaseModel):
    """Réponse pour un test manuel d'inférence sur une image uploadée (debug/QA)."""
    predicted_class: str
    confidence: float
    probabilities: dict
    processing_time_ms: float


class GradCAMResult(BaseModel):
    """Phase 5 — Explainable AI."""
    prediction_id: int
    predicted_class: str
    confidence: float
    original_image_url: str
    gradcam_image_url: str
