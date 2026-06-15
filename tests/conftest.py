"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

# Force a fresh in-memory SQLite for the test run, before app modules load.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_ENV", "testing")


@pytest.fixture
def client() -> TestClient:
    """A FastAPI test client. Sprint 1+ will add DB transaction rollback."""
    from app.main import app

    return TestClient(app)
