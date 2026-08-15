import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import cv2
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionRead, ManualPredictionResult, GradCAMResult
from app.services.ai_model import ai_model_service
from app.services.gradcam import gradcam_service, STATIC_DIR

router = APIRouter(prefix="/predictions", tags=["Predictions / Inspection History"])


@router.post("/test-image", response_model=ManualPredictionResult)
def test_prediction_on_image(
    file: UploadFile = File(...),
    _user=Depends(get_current_user),
):

    if not ai_model_service.model_loaded:
        raise HTTPException(
            503,
            f"Modèle non chargé. Placez final_model.keras dans le dossier configuré (MODEL_PATH).",
        )

    suffix = Path(file.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = ai_model_service.predict_from_file(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return result


@router.get("/", response_model=list[PredictionRead])
def list_predictions(
    machine_id: int | None = None,
    tool_id: int | None = None,
    predicted_class: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Historique d'inspection avec filtres — alimente la page Inspection History."""
    q = db.query(Prediction)
    if machine_id:
        q = q.filter(Prediction.machine_id == machine_id)
    if tool_id:
        q = q.filter(Prediction.tool_id == tool_id)
    if predicted_class:
        q = q.filter(Prediction.predicted_class == predicted_class)
    if date_from:
        q = q.filter(Prediction.created_at >= date_from)
    if date_to:
        q = q.filter(Prediction.created_at <= date_to)

    return q.order_by(Prediction.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{prediction_id}", response_model=PredictionRead)
def get_prediction(prediction_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Prediction).get(prediction_id)


@router.get("/{prediction_id}/gradcam", response_model=GradCAMResult)
def get_gradcam(prediction_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    prediction = db.query(Prediction).get(prediction_id)
    if not prediction:
        raise HTTPException(404, "Prédiction introuvable")
    if not prediction.frame_path:
        raise HTTPException(
            400,
            "Aucune frame originale n'a été sauvegardée pour cette prédiction "
            "(elle a probablement été créée avant l'activation de la Phase 5).",
        )
    if not ai_model_service.model_loaded:
        raise HTTPException(503, "Modèle IA non chargé — Grad-CAM indisponible.")

    if prediction.gradcam_path:
        return GradCAMResult(
            prediction_id=prediction.id,
            predicted_class=prediction.predicted_class,
            confidence=prediction.confidence,
            original_image_url=prediction.frame_path,
            gradcam_image_url=prediction.gradcam_path,
        )

    original_abs_path = STATIC_DIR / prediction.frame_path.replace("/static/", "", 1)
    frame_bgr = cv2.imread(str(original_abs_path))
    if frame_bgr is None:
        raise HTTPException(500, f"Impossible de relire la frame originale : {original_abs_path}")

    if prediction.predicted_class not in ai_model_service.class_names:
        raise HTTPException(500, "Classe prédite inconnue du service IA courant.")
    class_index = ai_model_service.class_names.index(prediction.predicted_class)

    tensor = ai_model_service.preprocess_from_bgr_frame(frame_bgr)
    _, gradcam_path = gradcam_service.generate_and_save(
        image_tensor=tensor,
        original_bgr=frame_bgr,
        class_index=class_index,
        prediction_id=prediction.id,
    )

    prediction.gradcam_path = gradcam_path
    db.commit()

    return GradCAMResult(
        prediction_id=prediction.id,
        predicted_class=prediction.predicted_class,
        confidence=prediction.confidence,
        original_image_url=prediction.frame_path,
        gradcam_image_url=gradcam_path,
    )
