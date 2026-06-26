from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Commit, Ticket
from ..schemas import CommitCreate, CommitOut, LinkItems
from typing import List

router = APIRouter(prefix="/commits", tags=["commits"])


@router.get("/", response_model=List[CommitOut])
def list_commits(db: Session = Depends(get_db)):
    return (db.query(Commit)
              .options(joinedload(Commit.author))
              .order_by(Commit.id.desc())
              .all())


@router.post("/", response_model=CommitOut, status_code=201)
def create_commit(body: CommitCreate, db: Session = Depends(get_db)):
    c = Commit(**body.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return c


@router.get("/{cid}", response_model=CommitOut)
def get_commit(cid: int, db: Session = Depends(get_db)):
    c = db.get(Commit, cid)
    if not c: raise HTTPException(404, "Commit not found")
    return c


@router.delete("/{cid}", status_code=204)
def delete_commit(cid: int, db: Session = Depends(get_db)):
    c = db.get(Commit, cid)
    if not c: raise HTTPException(404, "Commit not found")
    db.delete(c); db.commit()


@router.post("/{cid}/link-tickets", response_model=CommitOut)
def link_tickets(cid: int, body: LinkItems, db: Session = Depends(get_db)):
    c = db.get(Commit, cid)
    if not c: raise HTTPException(404, "Commit not found")
    tickets = db.query(Ticket).filter(Ticket.id.in_(body.ids)).all()
    c.tickets = list({*c.tickets, *tickets})
    db.commit(); db.refresh(c)
    return c
