"""Tests for database.py – covers the remaining uncovered lines."""
from unittest.mock import patch, MagicMock
import pytest


def test_init_db_calls_create_all():
    """init_db() should call Base.metadata.create_all with the engine."""
    from app import database
    with patch.object(database.Base.metadata, "create_all") as mock_create:
        database.init_db()
        mock_create.assert_called_once_with(bind=database.engine)


def test_get_db_yields_session_and_closes():
    """get_db() should yield a session and close it afterwards."""
    from app import database
    mock_session = MagicMock()
    with patch.object(database, "SessionLocal", return_value=mock_session):
        gen = database.get_db()
        session = next(gen)
        assert session is mock_session
        try:
            next(gen)
        except StopIteration:
            pass
        mock_session.close.assert_called_once()


def test_get_db_closes_on_exception():
    """get_db() should still close the session if an exception is raised."""
    from app import database
    mock_session = MagicMock()
    with patch.object(database, "SessionLocal", return_value=mock_session):
        gen = database.get_db()
        next(gen)
        try:
            gen.throw(RuntimeError("test error"))
        except RuntimeError:
            pass
        mock_session.close.assert_called_once()


def test_database_url_default():
    """DATABASE_URL should default to the expected PostgreSQL URL."""
    from app import database
    assert "postgresql" in database.DATABASE_URL or "sqlite" in database.DATABASE_URL


def test_session_local_created():
    """SessionLocal should be a callable factory."""
    from app.database import SessionLocal
    assert callable(SessionLocal)
