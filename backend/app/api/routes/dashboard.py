from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.machine import Machine, MachineStatus
from app.models.prediction import Prediction
from app.models.alert import Alert

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    machines_online = db.query(Machine).filter(Machine.status == MachineStatus.online).count()
    machines_total = db.query(Machine).count()

    today_alerts = db.query(Alert).filter(Alert.created_at >= today_start).count()

    last_prediction = (
        db.query(Prediction).order_by(Prediction.created_at.desc()).first()
    )

    recent_predictions = (
        db.query(Prediction).order_by(Prediction.created_at.desc()).limit(10).all()
    )

    class_distribution = (
        db.query(Prediction.predicted_class, func.count(Prediction.id))
        .group_by(Prediction.predicted_class)
        .all()
    )

    return {
        "machines_online": machines_online,
        "machines_total": machines_total,
        "todays_alerts": today_alerts,
        "last_inspection": {
            "predicted_class": last_prediction.predicted_class if last_prediction else None,
            "confidence": last_prediction.confidence if last_prediction else None,
            "created_at": last_prediction.created_at if last_prediction else None,
        },
        "recent_predictions": [
            {
                "id": p.id,
                "predicted_class": p.predicted_class,
                "confidence": p.confidence,
                "created_at": p.created_at,
                "machine_id": p.machine_id,
                "tool_id": p.tool_id,
            }
            for p in recent_predictions
        ],
        "class_distribution": {cls: count for cls, count in class_distribution},
    }
