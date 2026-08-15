from datetime import datetime
from pydantic import BaseModel
from app.models.machine import MachineStatus


class MachineCreate(BaseModel):
    name: str
    location: str | None = None
    camera_id: str | None = None


class MachineUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    camera_id: str | None = None
    status: MachineStatus | None = None


class MachineRead(BaseModel):
    id: int
    name: str
    location: str | None
    camera_id: str | None
    status: MachineStatus
    created_at: datetime

    class Config:
        from_attributes = True


class ToolCreate(BaseModel):
    machine_id: int
    tool_identifier: str
    tool_type: str | None = None


class ToolRead(BaseModel):
    id: int
    machine_id: int
    tool_identifier: str
    tool_type: str | None
    last_status: str | None
    last_inspection_at: datetime | None
    installed_at: datetime

    class Config:
        from_attributes = True
