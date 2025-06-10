"""Test module for RoleRepository"""

import pytest

from sqlalchemy.orm import Session

from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models import *
from asset_manager.repositories.role_repo import RoleRepository
from tests.data.model_creators import create_user
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


class TestRoleRepository:
    """Test suite for RoleRepository"""

    def test_get_roles_by_user_id_returns_correct_roles(self, db_session: Session):
        """Should return only roles that belong to the specified user"""
        repo = RoleRepository(db_session)

        user1 = create_user(db_session)
        user2 = create_user(db_session)

        repo.create({"user_id": user1.id, "role": "CreateEditUser", "scope": "*"})
        repo.create({"user_id": user2.id, "role": "ReadUser", "scope": "*"})

        roles_user1 = repo.get_roles_by_user_id(user1.id)
        assert len(roles_user1) == 1
        assert roles_user1[0].user_id == user1.id
        assert roles_user1[0].role == "CreateEditUser"

    def test_get_role_returns_matching_role(self, db_session: Session):
        """Should return the role object if exact match is found"""
        repo = RoleRepository(db_session)

        user = create_user(db_session)
        repo.create({"user_id": user.id, "role": "CreateEditUser", "scope": "*"})

        role_obj = repo.get_role(user.id, "CreateEditUser", "*")
        assert role_obj is not None
        assert role_obj.user_id == user.id
        assert role_obj.role == "CreateEditUser"
        assert role_obj.scope == "*"

    def test_get_role_returns_none_when_not_found(self, db_session: Session):
        """Should return None if no matching role exists"""
        repo = RoleRepository(db_session)

        user = create_user(db_session)
        repo.create({"user_id": user.id, "role": "ReadUser", "scope": "*"})

        result = repo.get_role(user.id, "DeleteUser", "*")
        assert result is None

        result = repo.get_role(user.id, "ReadUser", "department:HR")
        assert result is None
