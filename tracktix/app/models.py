from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Enum, Table, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

# ── Association tables ────────────────────────────────────────────────────────

ticket_requirement = Table(
    "ticket_requirement",
    Base.metadata,
    Column("ticket_id",      Integer, ForeignKey("tickets.id",      ondelete="CASCADE"), primary_key=True),
    Column("requirement_id", Integer, ForeignKey("requirements.id", ondelete="CASCADE"), primary_key=True),
)

ticket_commit = Table(
    "ticket_commit",
    Base.metadata,
    Column("ticket_id", Integer, ForeignKey("tickets.id",  ondelete="CASCADE"), primary_key=True),
    Column("commit_id",  Integer, ForeignKey("commits.id", ondelete="CASCADE"), primary_key=True),
)

ticket_test = Table(
    "ticket_test",
    Base.metadata,
    Column("ticket_id", Integer, ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("test_id",   Integer, ForeignKey("tests.id",   ondelete="CASCADE"), primary_key=True),
)

# ── Enums ─────────────────────────────────────────────────────────────────────

class TicketStatus(str, enum.Enum):
    open        = "open"
    in_progress = "in_progress"
    in_review   = "in_review"
    testing     = "testing"
    closed      = "closed"
    rejected    = "rejected"

class TicketPriority(str, enum.Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"

class TestResult(str, enum.Enum):
    pending = "pending"
    passed  = "passed"
    failed  = "failed"

class TestType(str, enum.Enum):
    unit        = "unit"
    integration = "integration"
    system      = "system"

# ── Models ────────────────────────────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"
    id          = Column(Integer, primary_key=True, index=True)
    key         = Column(String(16), unique=True, nullable=False)   # e.g. "PROJ"
    name        = Column(String(256), nullable=False)
    description = Column(Text, default="")
    git_base_url= Column(String(512), default="")                   # default remote for commits
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    tickets      = relationship("Ticket",      back_populates="project", cascade="all, delete")
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete")


class Requirement(Base):
    __tablename__ = "requirements"
    id          = Column(Integer, primary_key=True, index=True)
    project_id  = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key         = Column(String(64), nullable=False)      # e.g. "SRS-001"
    title       = Column(String(512), nullable=False)
    description = Column(Text, default="")
    url         = Column(String(1024), default="")        # hyperlink to external spec
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="requirements")
    tickets = relationship("Ticket",  secondary=ticket_requirement, back_populates="requirements")


class Person(Base):
    """A developer, tester, or analyst participating in the process."""
    __tablename__ = "persons"
    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(128), unique=True, nullable=False)
    full_name  = Column(String(256), default="")
    email      = Column(String(256), default="")
    git_server = Column(String(512), default="")   # e.g. https://github.com/username
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    commits  = relationship("Commit",  back_populates="author")
    tickets  = relationship("Ticket",  back_populates="assignee")
    comments = relationship("Comment", back_populates="author")
    tests    = relationship("Test",    back_populates="tester")


class Ticket(Base):
    __tablename__ = "tickets"
    id          = Column(Integer, primary_key=True, index=True)
    project_id  = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key         = Column(String(32), unique=True, nullable=False)   # e.g. "PROJ-42"
    title       = Column(String(512), nullable=False)
    description = Column(Text, default="")
    status      = Column(Enum(TicketStatus),   nullable=False, default=TicketStatus.open)
    priority    = Column(Enum(TicketPriority), nullable=False, default=TicketPriority.medium)
    assignee_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project      = relationship("Project",     back_populates="tickets")
    assignee     = relationship("Person",      back_populates="tickets")
    requirements = relationship("Requirement", secondary=ticket_requirement, back_populates="tickets")
    commits      = relationship("Commit",      secondary=ticket_commit, back_populates="tickets")
    tests        = relationship("Test",        secondary=ticket_test,   back_populates="tickets")
    comments     = relationship("Comment",     back_populates="ticket", cascade="all, delete", order_by="Comment.created_at")


class Commit(Base):
    __tablename__ = "commits"
    id          = Column(Integer, primary_key=True, index=True)
    sha         = Column(String(128), nullable=False)
    message     = Column(Text, default="")
    author_id   = Column(Integer, ForeignKey("persons.id"), nullable=True)
    git_url     = Column(String(1024), default="")   # direct link to commit on git server
    committed_at= Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    author  = relationship("Person", back_populates="commits")
    tickets = relationship("Ticket", secondary=ticket_commit, back_populates="commits")


class Test(Base):
    __tablename__ = "tests"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(512), nullable=False)
    description = Column(Text, default="")
    test_type   = Column(Enum(TestType),   nullable=False, default=TestType.unit)
    result      = Column(Enum(TestResult), nullable=False, default=TestResult.pending)
    tester_id   = Column(Integer, ForeignKey("persons.id"), nullable=True)
    run_at      = Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    tester  = relationship("Person", back_populates="tests")
    tickets = relationship("Ticket", secondary=ticket_test, back_populates="tests")


class Comment(Base):
    __tablename__ = "comments"
    id        = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    body      = Column(Text, nullable=False)
    created_at= Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket",  back_populates="comments")
    author = relationship("Person",  back_populates="comments")
