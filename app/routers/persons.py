from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Person
from ..schemas import PersonCreate, PersonOut
from typing import List

router = APIRouter(prefix="/persons", tags=["persons"])


@router.get("/", response_model=List[PersonOut])
def list_persons(db: Session = Depends(get_db)):
    return db.query(Person).order_by(Person.username).all()


@router.post("/", response_model=PersonOut, status_code=201)
def create_person(body: PersonCreate, db: Session = Depends(get_db)):
    if db.query(Person).filter(Person.username == body.username).first():
        raise HTTPException(400, "Username already exists")
    p = Person(**body.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p


@router.get("/{pid}", response_model=PersonOut)
def get_person(pid: int, db: Session = Depends(get_db)):
    p = db.get(Person, pid)
    if not p: raise HTTPException(404, "Person not found")
    return p


@router.put("/{pid}", response_model=PersonOut)
def update_person(pid: int, body: PersonCreate, db: Session = Depends(get_db)):
    p = db.get(Person, pid)
    if not p: raise HTTPException(404, "Person not found")
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return p


@router.delete("/{pid}", status_code=204)
def delete_person(pid: int, db: Session = Depends(get_db)):
    p = db.get(Person, pid)
    if not p: raise HTTPException(404, "Person not found")
    db.delete(p); db.commit()
