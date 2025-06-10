"""Test module for RequestRepository"""

import pytest

from sqlalchemy.orm import Session

from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models import *
from asset_manager.repositories.request_repo import RequestRepository
from tests.data.model_creators import (
    create_asset,
    create_request,
    create_user,
)
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


class TestRequestRepository:
    """Test suite for RequestRepository"""

    def test_get_requests_by_user(self, db_session: Session):
        """Ensure only requests for the given user are returned"""
        repo = RequestRepository(db_session)
        user1 = create_user(db_session)
        user2 = create_user(db_session)
        asset = create_asset(db_session)

        create_request(db_session, user_id=user1.id, asset_id=asset.id)
        create_request(db_session, user_id=user2.id, asset_id=asset.id)

        results = repo.get_requests_by_user(user1.id)
        assert len(results) == 1
        assert results[0].user_id == user1.id
