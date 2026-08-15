from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import require_admin
from app.models.settings import PlatformSettings
from app.schemas.settings import SettingsRead, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


def _get_or_create(db: Session) -> PlatformSettings:
    row = db.query(PlatformSettings).filter(PlatformSettings.id == 1).first()
    if not row:
        row = PlatformSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/", response_model=SettingsRead)
def get_settings(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return _get_or_create(db)


@router.put("/", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    row = _get_or_create(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row
