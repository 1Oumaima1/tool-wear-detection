from datetime import datetime
from pydantic import BaseModel
from app.models.report import ReportType


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    period_start: datetime | None = None  # sinon calculé automatiquement selon report_type
    period_end: datetime | None = None


class ReportRead(BaseModel):
    id: int
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True
