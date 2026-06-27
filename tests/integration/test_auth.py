"""Integration tests for B-01: login, logout, route guards, role enforcement."""

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.shift import Role, User
from app.services.auth_service import hash_password


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    db.add_all(
        [
            User(
                username="operator1",
                password_hash=hash_password("operator1"),
                role=Role.OPERATOR,
            ),
            User(
                username="super1",
                password_hash=hash_password("super1"),
                role=Role.SUPERVISOR,
            ),
            User(
                username="admin",
                password_hash=hash_password("admin"),
                role=Role.ADMIN,
            ),
        ]
    )
    db.commit()
    db.close()
    yield


def _client() -> TestClient:
    # A fresh client per test so cookie/session state never leaks between tests.
    return TestClient(app)


def test_login_page_renders():
    c = _client()
    r = c.get("/login")
    assert r.status_code == 200
    assert "Log in" in r.text


def test_login_success_sets_session_and_redirects():
    c = _client()
    r = c.post(
        "/login",
        data={"username": "operator1", "password": "operator1", "next": ""},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    # Session cookie was issued.
    assert c.cookies.get("bottling_session") is not None


def test_login_failure_shows_generic_error():
    c = _client()
    r = c.post(
        "/login",
        data={"username": "operator1", "password": "wrong", "next": ""},
    )
    assert r.status_code == 401
    assert "Invalid username or password" in r.text


def test_protected_route_redirects_anonymous_to_login():
    c = _client()
    r = c.get("/operator/shift/new", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/login")
    # The original destination is preserved for post-login redirect.
    assert "next=" in r.headers["location"]


def test_login_then_access_protected_route():
    c = _client()
    c.post("/login", data={"username": "operator1", "password": "operator1"})
    r = c.get("/operator/shift/new")
    assert r.status_code == 200
    assert "Open a Shift" in r.text


def test_next_param_returns_user_to_destination():
    c = _client()
    r = c.post(
        "/login",
        data={
            "username": "operator1",
            "password": "operator1",
            "next": "/operator/shifts",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/operator/shifts"


def test_open_redirect_is_blocked():
    c = _client()
    r = c.post(
        "/login",
        data={"username": "operator1", "password": "operator1", "next": "//evil.example"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_supervisor_allowed_on_operator_screen():
    c = _client()
    c.post("/login", data={"username": "super1", "password": "super1"})
    r = c.get("/operator/shift/new")
    assert r.status_code == 200


def test_admin_allowed_on_operator_screen():
    c = _client()
    c.post("/login", data={"username": "admin", "password": "admin"})
    r = c.get("/operator/shift/new")
    assert r.status_code == 200


def test_logout_clears_session():
    c = _client()
    c.post("/login", data={"username": "operator1", "password": "operator1"})
    r = c.post("/logout", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"
    # Now blocked again.
    r2 = c.get("/operator/shift/new", follow_redirects=False)
    assert r2.status_code == 303
    assert r2.headers["location"].startswith("/login")


def test_logged_in_home_shows_username():
    c = _client()
    c.post("/login", data={"username": "operator1", "password": "operator1"})
    r = c.get("/")
    assert r.status_code == 200
    assert "operator1" in r.text
    assert "Log out" in r.text


def test_already_logged_in_login_page_redirects():
    c = _client()
    c.post("/login", data={"username": "operator1", "password": "operator1"})
    r = c.get("/login", follow_redirects=False)
    assert r.status_code == 303
