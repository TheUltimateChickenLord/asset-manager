"""Tests for authorization utility functions"""

import pytest

from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from asset_manager.core.authz_utils import (
    get_assets_by_labels,
    get_labels_by_roles,
    get_users_by_labels,
)
from asset_manager.db import session
from asset_manager.db.base import Base
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


class TestAuthzUtils:
    def test_get_assets_by_labels_expression(self):
        """Test that get_assets_by_labels returns a SQLAlchemy boolean expression"""
        result = get_assets_by_labels([1, 2, 3])
        assert hasattr(result, "compile")  # Should be a valid SQLAlchemy clause element

    def test_get_users_by_labels_expression(self):
        """Test that get_assets_by_labels returns a SQLAlchemy boolean expression"""
        result = get_users_by_labels([1, 2, 3])
        assert hasattr(result, "compile")  # Should be a valid SQLAlchemy clause element

    def test_get_labels_by_roles_returns_ids_correctly(self):
        """Test that get_labels_by_roles returns list of label IDs for matching names"""
        db = MagicMock(spec=Session)
        db.query().filter().all.return_value = [(1,), (2,)]

        result = get_labels_by_roles(db, ["Admin", "Editor"])
        assert result == [1, 2]
        db.query().filter().all.assert_called_once()
