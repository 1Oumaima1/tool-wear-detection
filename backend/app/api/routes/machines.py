from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.machine import Machine
from app.models.tool import Tool
from app.schemas.machine import MachineCreate, MachineUpdate, MachineRead, ToolCreate, ToolRead

router = APIRouter(prefix="/machines", tags=["Machines"])


@router.get("/", response_model=list[MachineRead])
def list_machines(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Machine).all()


@router.post("/", response_model=MachineRead, status_code=201)
def create_machine(payload: MachineCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    machine = Machine(**payload.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.get("/{machine_id}", response_model=MachineRead)
def get_machine(machine_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    machine = db.query(Machine).get(machine_id)
    if not machine:
        raise HTTPException(404, "Machine introuvable")
    return machine


@router.patch("/{machine_id}", response_model=MachineRead)
def update_machine(machine_id: int, payload: MachineUpdate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    machine = db.query(Machine).get(machine_id)
    if not machine:
        raise HTTPException(404, "Machine introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(machine, field, value)
    db.commit()
    db.refresh(machine)
    return machine


@router.delete("/{machine_id}", status_code=204)
def delete_machine(machine_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    machine = db.query(Machine).get(machine_id)
    if not machine:
        raise HTTPException(404, "Machine introuvable")
    db.delete(machine)
    db.commit()


# --- Tools (rattachés à une machine) ---

@router.post("/{machine_id}/tools", response_model=ToolRead, status_code=201)
def create_tool(machine_id: int, payload: ToolCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    if payload.machine_id != machine_id:
        raise HTTPException(400, "machine_id incohérent")
    tool = Tool(**payload.model_dump())
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return tool


@router.get("/{machine_id}/tools", response_model=list[ToolRead])
def list_tools(machine_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Tool).filter(Tool.machine_id == machine_id).all()
