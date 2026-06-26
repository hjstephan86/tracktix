from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Project
from ..schemas import ProjectCreate, ProjectOut
from typing import List

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id).all()


@router.post("/", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    if db.query(Project).filter(Project.key == body.key.upper()).first():
        raise HTTPException(400, "Project key already exists")
    data = body.model_dump()
    data["key"] = body.key.upper()
    proj = Project(**data)
    db.add(proj); db.commit(); db.refresh(proj)
    return proj


@router.get("/{pid}", response_model=ProjectOut)
def get_project(pid: int, db: Session = Depends(get_db)):
    p = db.get(Project, pid)
    if not p: raise HTTPException(404, "Project not found")
    return p


@router.put("/{pid}", response_model=ProjectOut)
def update_project(pid: int, body: ProjectCreate, db: Session = Depends(get_db)):
    p = db.get(Project, pid)
    if not p: raise HTTPException(404, "Project not found")
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return p


@router.delete("/{pid}", status_code=204)
def delete_project(pid: int, db: Session = Depends(get_db)):
    p = db.get(Project, pid)
    if not p: raise HTTPException(404, "Project not found")
    db.delete(p); db.commit()
