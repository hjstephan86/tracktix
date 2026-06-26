from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Requirement
from ..schemas import RequirementCreate, RequirementOut
from typing import List

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.get("/", response_model=List[RequirementOut])
def list_requirements(project_id: int = None, db: Session = Depends(get_db)):
    q = db.query(Requirement)
    if project_id:
        q = q.filter(Requirement.project_id == project_id)
    return q.order_by(Requirement.key).all()


@router.post("/", response_model=RequirementOut, status_code=201)
def create_requirement(body: RequirementCreate, db: Session = Depends(get_db)):
    r = Requirement(**body.model_dump())
    db.add(r); db.commit(); db.refresh(r)
    return r


@router.get("/{rid}", response_model=RequirementOut)
def get_requirement(rid: int, db: Session = Depends(get_db)):
    r = db.get(Requirement, rid)
    if not r: raise HTTPException(404, "Requirement not found")
    return r


@router.put("/{rid}", response_model=RequirementOut)
def update_requirement(rid: int, body: RequirementCreate, db: Session = Depends(get_db)):
    r = db.get(Requirement, rid)
    if not r: raise HTTPException(404, "Requirement not found")
    for k, v in body.model_dump().items():
        setattr(r, k, v)
    db.commit(); db.refresh(r)
    return r


@router.delete("/{rid}", status_code=204)
def delete_requirement(rid: int, db: Session = Depends(get_db)):
    r = db.get(Requirement, rid)
    if not r: raise HTTPException(404, "Requirement not found")
    db.delete(r); db.commit()
