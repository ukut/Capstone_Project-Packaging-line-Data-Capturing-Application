"""Unit tests for the auth service: password hashing and credential checks."""

import pytest

from app.database import Base, SessionLocal, engine
from app.dependencies import ForbiddenError, require_role
from app.models.shift import Role, User
from app.services.auth_service import AuthService, hash_password, verify_password


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def test_hash_is_not_plaintext_and_verifies():
    h = hash_password("s3cret")
    assert h != "s3cret"
    assert verify_password("s3cret", h) is True


def test_verify_rejects_wrong_password():
    h = hash_password("s3cret")
    assert verify_password("wrong", h) is False


def test_verify_handles_malformed_hash_without_raising():
    # A legacy/garbage hash must fail closed, not crash the login route.
    assert verify_password("anything", "not-a-bcrypt-hash") is False


def test_hashes_are_salted_and_differ():
    assert hash_password("same") != hash_password("same")


def _make_user(db, username="operator1", password="operator1", active=True):
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=Role.OPERATOR,
        is_active=active,
    )
    db.add(user)
    db.commit()
    return user


def test_authenticate_success_returns_user():
    db = SessionLocal()
    _make_user(db)
    user = AuthService(db).authenticate("operator1", "operator1")
    assert user is not None
    assert user.username == "operator1"
    db.close()


def test_authenticate_wrong_password_returns_none():
    db = SessionLocal()
    _make_user(db)
    assert AuthService(db).authenticate("operator1", "nope") is None
    db.close()


def test_authenticate_unknown_user_returns_none():
    db = SessionLocal()
    assert AuthService(db).authenticate("ghost", "whatever") is None
    db.close()


def test_authenticate_inactive_user_returns_none():
    db = SessionLocal()
    _make_user(db, username="gone", password="pw", active=False)
    assert AuthService(db).authenticate("gone", "pw") is None
    db.close()


def test_require_role_rejects_wrong_role():
    dep = require_role(Role.ADMIN)
    operator = User(username="op", password_hash="x", role=Role.OPERATOR, is_active=True)
    with pytest.raises(ForbiddenError):
        dep(user=operator)


def test_require_role_allows_matching_role():
    dep = require_role(Role.ADMIN, Role.SUPERVISOR)
    sup = User(username="s", password_hash="x", role=Role.SUPERVISOR, is_active=True)
    assert dep(user=sup) is sup
