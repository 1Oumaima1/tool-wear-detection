from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.alert import Alert
from app.schemas.prediction import AlertRead

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertRead])
def list_alerts(
    resolved: bool | None = None,
    machine_id: int | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Alert)
    if resolved is not None:
        q = q.filter(Alert.resolved == resolved)
    if machine_id:
        q = q.filter(Alert.machine_id == machine_id)
    return q.order_by(Alert.created_at.desc()).all()


@router.patch("/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(alert_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    alert = db.query(Alert).get(alert_id)
    if not alert:
        raise HTTPException(404, "Alerte introuvable")
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert
