"""
Shared pytest fixtures for TrackTix test suite.

Two test layers:
  1. API tests  – use TestClient with an in-memory SQLite database
  2. E2E tests  – use Playwright against a live Uvicorn server + SQLite
"""
import threading
import time
import socket
import pytest
import uvicorn
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.database import get_db
from app.main import app


# ── SQLite engine (API tests) ─────────────────────────────────────────────────

SQLITE_URL = "sqlite:///./test_tracktix.db"
_engine_api = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
_SessionAPI = sessionmaker(autocommit=False, autoflush=False, bind=_engine_api)


def _override_get_db_api():
    db = _SessionAPI()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=_engine_api)
    app.dependency_overrides[get_db] = _override_get_db_api
    with patch("app.main.init_db", return_value=None):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine_api)


# ── API helper fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def project(client):
    r = client.post("/api/projects/", json={
        "key": "TEST", "name": "Test Project",
        "description": "desc", "git_base_url": "https://github.com/user/repo",
    })
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def requirement(client, project):
    r = client.post("/api/requirements/", json={
        "project_id": project["id"], "key": "SRS-001",
        "title": "The system shall do X", "description": "Full description",
        "url": "https://spec.example.com/SRS-001",
    })
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def person(client):
    r = client.post("/api/persons/", json={
        "username": "jdoe", "full_name": "Jane Doe",
        "email": "jane@example.com", "git_server": "https://github.com/jdoe",
    })
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def commit(client, person):
    r = client.post("/api/commits/", json={
        "sha": "abc1234567890abcdef",
        "message": "feat: implement feature X\n\nDetails here.",
        "author_id": person["id"],
        "git_url": "https://github.com/user/repo/commit/abc1234567890abcdef",
        "committed_at": "2024-06-01T10:00:00Z",
    })
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def test_obj(client, person):
    r = client.post("/api/tests/", json={
        "title": "Unit test for feature X", "description": "Tests the main path",
        "test_type": "unit", "result": "passed",
        "tester_id": person["id"], "run_at": "2024-06-02T09:00:00Z",
    })
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def ticket(client, project, requirement):
    r = client.post("/api/tickets/", json={
        "project_id": project["id"], "title": "Implement feature X",
        "description": "As described in SRS-001",
        "status": "open", "priority": "high",
        "requirement_ids": [requirement["id"]],
    })
    assert r.status_code == 201
    return r.json()


# ── Live Uvicorn server for Playwright E2E tests ──────────────────────────────

E2E_SQLITE_URL = "sqlite:///./test_e2e_tracktix.db"
_engine_e2e = create_engine(E2E_SQLITE_URL, connect_args={"check_same_thread": False})
_SessionE2E = sessionmaker(autocommit=False, autoflush=False, bind=_engine_e2e)


def _override_get_db_e2e():
    db = _SessionE2E()
    try:
        yield db
    finally:
        db.close()


class _Server(uvicorn.Server):
    def install_signal_handlers(self):
        pass


@pytest.fixture(scope="session")
def live_server():
    Base.metadata.create_all(bind=_engine_e2e)
    app.dependency_overrides[get_db] = _override_get_db_e2e

    with patch("app.main.init_db", return_value=None):
        config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="error")
        server = _Server(config=config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                socket.create_connection(("127.0.0.1", 8765), timeout=0.3).close()
                break
            except OSError:
                time.sleep(0.1)

        yield "http://127.0.0.1:8765"

        server.should_exit = True
        thread.join(timeout=5)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine_e2e)
