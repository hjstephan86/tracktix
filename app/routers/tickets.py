from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Ticket, Project, Requirement, Commit, Test, Comment, Person
from ..schemas import (
    TicketCreate, TicketUpdate, TicketOut, TicketListOut,
    CommentCreate, CommentOut, LinkItems
)
from typing import List, Optional

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _next_key(db: Session, project: Project) -> str:
    count = db.query(Ticket).filter(Ticket.project_id == project.id).count()
    return f"{project.key}-{count + 1}"


def _load_ticket(db: Session, tid: int) -> Ticket:
    t = (db.query(Ticket)
           .options(
               joinedload(Ticket.assignee),
               joinedload(Ticket.requirements),
               joinedload(Ticket.commits).joinedload(Commit.author),
               joinedload(Ticket.tests).joinedload(Test.tester),
               joinedload(Ticket.comments).joinedload(Comment.author),
           )
           .filter(Ticket.id == tid)
           .first())
    if not t:
        raise HTTPException(404, "Ticket not found")
    return t


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[TicketListOut])
def list_tickets(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = (db.query(Ticket)
           .options(joinedload(Ticket.assignee),
                    joinedload(Ticket.requirements),
                    joinedload(Ticket.commits),
                    joinedload(Ticket.tests)))
    if project_id:  q = q.filter(Ticket.project_id == project_id)
    if status:      q = q.filter(Ticket.status == status)
    if priority:    q = q.filter(Ticket.priority == priority)
    if assignee_id: q = q.filter(Ticket.assignee_id == assignee_id)
    if search:
        like = f"%{search}%"
        q = q.filter(Ticket.title.ilike(like) | Ticket.description.ilike(like) | Ticket.key.ilike(like))

    tickets = q.order_by(Ticket.id.desc()).all()
    result = []
    for t in tickets:
        d = TicketListOut.model_validate(t)
        d.req_count    = len(t.requirements)
        d.commit_count = len(t.commits)
        d.test_count   = len(t.tests)
        result.append(d)
    return result


@router.post("/", response_model=TicketOut, status_code=201)
def create_ticket(body: TicketCreate, db: Session = Depends(get_db)):
    proj = db.get(Project, body.project_id)
    if not proj: raise HTTPException(404, "Project not found")
    key = _next_key(db, proj)
    reqs = db.query(Requirement).filter(Requirement.id.in_(body.requirement_ids)).all()
    data = body.model_dump(exclude={"requirement_ids"})
    t = Ticket(**data, key=key, requirements=reqs)
    db.add(t); db.commit(); db.refresh(t)
    return _load_ticket(db, t.id)


@router.get("/{tid}", response_model=TicketOut)
def get_ticket(tid: int, db: Session = Depends(get_db)):
    return _load_ticket(db, tid)


@router.put("/{tid}", response_model=TicketOut)
def update_ticket(tid: int, body: TicketUpdate, db: Session = Depends(get_db)):
    t = db.get(Ticket, tid)
    if not t: raise HTTPException(404, "Ticket not found")
    data = body.model_dump(exclude_unset=True, exclude={"requirement_ids"})
    for k, v in data.items():
        setattr(t, k, v)
    if body.requirement_ids is not None:
        t.requirements = db.query(Requirement).filter(Requirement.id.in_(body.requirement_ids)).all()
    db.commit()
    return _load_ticket(db, t.id)


@router.delete("/{tid}", status_code=204)
def delete_ticket(tid: int, db: Session = Depends(get_db)):
    t = db.get(Ticket, tid)
    if not t: raise HTTPException(404, "Ticket not found")
    db.delete(t); db.commit()


# ── Link endpoints ────────────────────────────────────────────────────────────

@router.post("/{tid}/commits", response_model=TicketOut)
def link_commits(tid: int, body: LinkItems, db: Session = Depends(get_db)):
    t = db.get(Ticket, tid)
    if not t: raise HTTPException(404, "Ticket not found")
    commits = db.query(Commit).filter(Commit.id.in_(body.ids)).all()
    t.commits = list({*t.commits, *commits})
    db.commit()
    return _load_ticket(db, t.id)


@router.delete("/{tid}/commits/{cid}", response_model=TicketOut)
def unlink_commit(tid: int, cid: int, db: Session = Depends(get_db)):
    t = db.get(Ticket, tid)
    if not t: raise HTTPException(404, "Ticket not found")
    t.commits = [c for c in t.commits if c.id != cid]
    db.commit()
    return _load_ticket(db, t.id)


@router.post("/{tid}/tests", response_model=TicketOut)
def link_tests(tid: int, body: LinkItems, db: Session = Depends(get_db)):
    t = db.get(Ticket, tid)
    if not t: raise HTTPException(404, "Ticket not found")
    tests = db.query(Test).filter(Test.id.in_(body.ids)).all()
    t.tests = list({*t.tests, *tests})
    db.commit()
    return _load_ticket(db, t.id)


@router.delete("/{tid}/tests/{test_id}", response_model=TicketOut)
def unlink_test(tid: int, test_id: int, db: Session = Depends(get_db)):
    t = db.get(Ticket, tid)
    if not t: raise HTTPException(404, "Ticket not found")
    t.tests = [x for x in t.tests if x.id != test_id]
    db.commit()
    return _load_ticket(db, t.id)


# ── Comments ──────────────────────────────────────────────────────────────────

@router.post("/{tid}/comments", response_model=CommentOut, status_code=201)
def add_comment(tid: int, body: CommentCreate, db: Session = Depends(get_db)):
    t = db.get(Ticket, tid)
    if not t: raise HTTPException(404, "Ticket not found")
    c = Comment(ticket_id=tid, **body.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return c


@router.delete("/{tid}/comments/{cid}", status_code=204)
def delete_comment(tid: int, cid: int, db: Session = Depends(get_db)):
    c = db.get(Comment, cid)
    if not c or c.ticket_id != tid: raise HTTPException(404, "Comment not found")
    db.delete(c); db.commit()


# ── Traceability ──────────────────────────────────────────────────────────────

@router.get("/{tid}/traceability")
def traceability(tid: int, db: Session = Depends(get_db)):
    """Return the full traceability chain for a ticket."""
    t = _load_ticket(db, tid)
    return {
        "ticket": {
            "id": t.id, "key": t.key, "title": t.title,
            "status": t.status, "priority": t.priority,
        },
        "requirements": [
            {"id": r.id, "key": r.key, "title": r.title, "url": r.url}
            for r in t.requirements
        ],
        "commits": [
            {
                "id": c.id,
                "sha": c.sha[:12] if c.sha else "",
                "message": c.message,
                "git_url": c.git_url,
                "author": c.author.username if c.author else None,
                "committed_at": c.committed_at.isoformat() if c.committed_at else None,
            }
            for c in sorted(t.commits, key=lambda x: x.committed_at or x.created_at)
        ],
        "tests": [
            {
                "id": x.id,
                "title": x.title,
                "type": x.test_type,
                "result": x.result,
                "tester": x.tester.username if x.tester else None,
                "run_at": x.run_at.isoformat() if x.run_at else None,
            }
            for x in t.tests
        ],
    }
