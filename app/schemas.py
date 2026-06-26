from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, List
from datetime import datetime
from .models import TicketStatus, TicketPriority, TestResult, TestType

# ── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    key: str
    name: str
    description: str = ""
    git_base_url: str = ""

class ProjectOut(ProjectCreate):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}

# ── Requirement ───────────────────────────────────────────────────────────────

class RequirementCreate(BaseModel):
    project_id: int
    key: str
    title: str
    description: str = ""
    url: str = ""

class RequirementOut(RequirementCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

# ── Person ────────────────────────────────────────────────────────────────────

class PersonCreate(BaseModel):
    username: str
    full_name: str = ""
    email: str = ""
    git_server: str = ""

class PersonOut(PersonCreate):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}

# ── Commit ────────────────────────────────────────────────────────────────────

class CommitCreate(BaseModel):
    sha: str
    message: str = ""
    author_id: Optional[int] = None
    git_url: str = ""
    committed_at: Optional[datetime] = None

class CommitOut(CommitCreate):
    id: int
    created_at: datetime
    author: Optional[PersonOut] = None
    model_config = {"from_attributes": True}

# ── Test ──────────────────────────────────────────────────────────────────────

class TestCreate(BaseModel):
    title: str
    description: str = ""
    test_type: TestType = TestType.unit
    result: TestResult = TestResult.pending
    tester_id: Optional[int] = None
    run_at: Optional[datetime] = None

class TestOut(TestCreate):
    id: int
    created_at: datetime
    tester: Optional[PersonOut] = None
    model_config = {"from_attributes": True}

# ── Comment ───────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    body: str
    author_id: Optional[int] = None

class CommentOut(CommentCreate):
    id: int
    ticket_id: int
    created_at: datetime
    author: Optional[PersonOut] = None
    model_config = {"from_attributes": True}

# ── Ticket ────────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    project_id: int
    title: str
    description: str = ""
    status: TicketStatus = TicketStatus.open
    priority: TicketPriority = TicketPriority.medium
    assignee_id: Optional[int] = None
    requirement_ids: List[int] = []

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assignee_id: Optional[int] = None
    requirement_ids: Optional[List[int]] = None

class TicketOut(BaseModel):
    id: int
    key: str
    project_id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    assignee: Optional[PersonOut] = None
    requirements: List[RequirementOut] = []
    commits: List[CommitOut] = []
    tests: List[TestOut] = []
    comments: List[CommentOut] = []
    model_config = {"from_attributes": True}

class TicketListOut(BaseModel):
    id: int
    key: str
    title: str
    status: TicketStatus
    priority: TicketPriority
    project_id: int
    assignee: Optional[PersonOut] = None
    created_at: datetime
    updated_at: datetime
    req_count: int = 0
    commit_count: int = 0
    test_count: int = 0
    model_config = {"from_attributes": True}

# ── Link helpers ──────────────────────────────────────────────────────────────

class LinkItems(BaseModel):
    ids: List[int]
