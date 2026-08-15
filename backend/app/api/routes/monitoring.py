import logging
from datetime import datetime
from pathlib import Path

import cv2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.prediction import Prediction
from app.models.tool import Tool
from app.models.machine import Machine
from app.services.video_processor import video_processor
from app.services.ai_model import ai_model_service
from app.services.decision_engine import decision_engine
from app.services.gradcam import ORIGINALS_DIR

logger = logging.getLogger("monitoring")
router = APIRouter(prefix="/monitoring", tags=["Live Monitoring (Phase 2)"])


class ProcessVideoRequest(BaseModel):
    video_filename: str          # ex: "cnc_camera_01.mp4" (dans le dossier videos/)
    machine_id: int
    tool_id: int
    frame_interval_seconds: float | None = None   # sinon valeur par défaut des settings
    max_frames: int | None = None                  # utile pour tester sur un extrait


class FramePredictionOut(BaseModel):
    prediction_id: int
    frame_index: int
    timestamp_seconds: float
    predicted_class: str
    confidence: float
    processing_time_ms: float
    frame_path: str | None = None


class ProcessVideoResponse(BaseModel):
    video_filename: str
    frames_processed: int
    predictions: list[FramePredictionOut]
    alerts_created: list[int]


@router.get("/videos")
def list_videos(_user=Depends(get_current_user)):
    """Liste les fichiers vidéo présents dans le dossier videos/."""
    return {"videos": video_processor.list_videos(), "folder": str(video_processor.video_folder)}


@router.post("/process-video", response_model=ProcessVideoResponse)
def process_video(
    payload: ProcessVideoRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if not ai_model_service.model_loaded:
        raise HTTPException(
            503,
            "Modèle IA non chargé — dépose final_model.keras à l'emplacement configuré (MODEL_PATH) "
            "puis redémarre l'API avant de lancer le monitoring vidéo.",
        )

    machine = db.query(Machine).get(payload.machine_id)
    tool = db.query(Tool).get(payload.tool_id)
    if not machine or not tool:
        raise HTTPException(404, "machine_id ou tool_id introuvable")

    try:
        frames = video_processor.extract_frames(
            video_filename=payload.video_filename,
            frame_interval_seconds=payload.frame_interval_seconds,
            max_frames=payload.max_frames,
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(400, str(e))

    predictions_out: list[FramePredictionOut] = []
    alerts_created: list[int] = []

    for extracted in frames:
        result = ai_model_service.predict_from_bgr_frame(extracted.frame_bgr)

        prediction = Prediction(
            machine_id=payload.machine_id,
            tool_id=payload.tool_id,
            predicted_class=result["predicted_class"],
            confidence=result["confidence"],
            probabilities=result["probabilities"],
            source="video",
            processing_time_ms=result["processing_time_ms"],
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        # Sauvegarde la frame originale sur disque (utilisée à la demande par
        # Grad-CAM en Phase 5 — on ne génère pas la heatmap ici pour ne pas
        # ralentir le traitement de toute la vidéo frame par frame).
        original_filename = f"pred_{prediction.id}_original.jpg"
        cv2.imwrite(str(ORIGINALS_DIR / original_filename), extracted.frame_bgr)
        prediction.frame_path = f"/static/frames/{original_filename}"
        db.commit()

        # Met à jour le statut courant de l'outil à chaque frame (pas seulement en cas d'alerte)
        tool.last_status = prediction.predicted_class
        tool.last_inspection_at = datetime.utcnow()
        db.commit()

        alert = decision_engine.evaluate(db, prediction)
        if alert:
            alerts_created.append(alert.id)

        predictions_out.append(FramePredictionOut(
            prediction_id=prediction.id,
            frame_index=extracted.frame_index,
            timestamp_seconds=round(extracted.timestamp_seconds, 2),
            predicted_class=result["predicted_class"],
            confidence=result["confidence"],
            processing_time_ms=result["processing_time_ms"],
            frame_path=prediction.frame_path,
        ))

    logger.info(
        "Vidéo %s traitée : %d frames, %d alerte(s) créée(s)",
        payload.video_filename, len(predictions_out), len(alerts_created),
    )

    return ProcessVideoResponse(
        video_filename=payload.video_filename,
        frames_processed=len(predictions_out),
        predictions=predictions_out,
        alerts_created=alerts_created,
    )
