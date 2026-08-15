from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.report import Report
from app.schemas.report import ReportGenerateRequest, ReportRead
from app.services.reports_service import generate_report

router = APIRouter(prefix="/reports", tags=["Reports (Phase 6)"])


@router.post("/generate", response_model=ReportRead, status_code=201)
def generate(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    
    report = generate_report(
        db,
        report_type=payload.report_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    return report


@router.get("/", response_model=list[ReportRead])
def list_reports(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    report = db.query(Report).get(report_id)
    if not report:
        raise HTTPException(404, "Rapport introuvable")
    path = Path(report.file_path)
    if not path.exists():
        raise HTTPException(404, "Le fichier PDF n'existe plus sur le disque du serveur.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
