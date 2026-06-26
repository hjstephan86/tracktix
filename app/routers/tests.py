from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Test, Ticket
from ..schemas import TestCreate, TestOut, LinkItems
from typing import List

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("/", response_model=List[TestOut])
def list_tests(db: Session = Depends(get_db)):
    return (db.query(Test)
              .options(joinedload(Test.tester))
              .order_by(Test.id.desc())
              .all())


@router.post("/", response_model=TestOut, status_code=201)
def create_test(body: TestCreate, db: Session = Depends(get_db)):
    t = Test(**body.model_dump())
    db.add(t); db.commit(); db.refresh(t)
    return t


@router.get("/{tid}", response_model=TestOut)
def get_test(tid: int, db: Session = Depends(get_db)):
    t = db.get(Test, tid)
    if not t: raise HTTPException(404, "Test not found")
    return t


@router.put("/{tid}", response_model=TestOut)
def update_test(tid: int, body: TestCreate, db: Session = Depends(get_db)):
    t = db.get(Test, tid)
    if not t: raise HTTPException(404, "Test not found")
    for k, v in body.model_dump().items():
        setattr(t, k, v)
    db.commit(); db.refresh(t)
    return t


@router.delete("/{tid}", status_code=204)
def delete_test(tid: int, db: Session = Depends(get_db)):
    t = db.get(Test, tid)
    if not t: raise HTTPException(404, "Test not found")
    db.delete(t); db.commit()


@router.post("/{tid}/link-tickets", response_model=TestOut)
def link_tickets(tid: int, body: LinkItems, db: Session = Depends(get_db)):
    t = db.get(Test, tid)
    if not t: raise HTTPException(404, "Test not found")
    tickets = db.query(Ticket).filter(Ticket.id.in_(body.ids)).all()
    t.tickets = list({*t.tickets, *tickets})
    db.commit(); db.refresh(t)
    return t
