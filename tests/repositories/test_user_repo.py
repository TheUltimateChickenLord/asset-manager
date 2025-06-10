"""Test module for UserRepository"""

import pytest

from sqlalchemy.orm import Session

from asset_manager.db import session
from asset_manager.core.security import verify_password
from asset_manager.db.base import Base
from asset_manager.db.models import *
from asset_manager.repositories.user_repo import UserRepository
from tests.data.reload import reload_all_modules


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch: pytest.MonkeyPatch):
    """Fixture set the database to in-memory for testing"""
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("LOG_DIR", "tests/logs")
    reload_all_modules()


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to create a new database session for testing
    Automatically tears down the schema after each test
    """
    current_session = session.SessionLocal()
    Base.metadata.create_all(bind=session.engine)
    yield current_session
    current_session.close()
    Base.metadata.drop_all(bind=session.engine)


class TestUserRepository:
    """Test suite for UserRepository"""

    def test_register_user_creates_user_with_hashed_password(self, db_session: Session):
        """Should create user with hashed password and salt"""
        repo = UserRepository(db_session)
        repo.register_user("Alice", "alice@example.com", "securepassword")
        db_session.expunge_all()

        fetched = repo.get_by_email("alice@example.com")
        assert fetched is not None
        assert fetched.name == "Alice"
        assert fetched.email == "alice@example.com"
        assert fetched.password_hash != "securepassword"
        assert fetched.password_salt
        assert verify_password(
            "securepassword", fetched.password_salt, fetched.password_hash
        )

    def test_get_by_email_returns_correct_user(self, db_session: Session):
        """Should retrieve the correct user by email"""
        repo = UserRepository(db_session)
        repo.register_user("Bob", "bob@example.com", "pass123")
        user = repo.get_by_email("bob@example.com")
        assert user is not None
        assert user.name == "Bob"

    def test_get_by_name_returns_correct_user(self, db_session: Session):
        """Should retrieve the correct user by name"""
        repo = UserRepository(db_session)
        repo.register_user("Charlie", "charlie@example.com", "pass123")
        user = repo.get_by_name("Charlie")
        assert user is not None
        assert user.email == "charlie@example.com"

    def test_disable_enable_user_sets_flag(self, db_session: Session):
        """Should mark the user as disabled then enabled"""
        repo = UserRepository(db_session)
        user = repo.register_user("Dora", "dora@example.com", "pass123")
        updated = repo.disable_user(user)
        assert updated.is_disabled is True
        updated = repo.enable_user(user)
        assert updated.is_disabled is False

    def test_reset_password_changes_hash_and_salt(self, db_session: Session):
        """Should change both password hash and salt when resetting password"""
        repo = UserRepository(db_session)
        user = repo.register_user("Eve", "eve@example.com", "oldpass")
        old_hash = user.password_hash
        old_salt = user.password_salt

        updated = repo.reset_password(user, "newpass123")
        assert updated.password_hash != old_hash
        assert updated.password_salt != old_salt
        assert verify_password(
            "newpass123", updated.password_salt, updated.password_hash
        )
