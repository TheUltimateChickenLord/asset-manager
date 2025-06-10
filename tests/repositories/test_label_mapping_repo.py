"""Test module for LabelMappingAssetRepository and LabelMappingUserRepository"""

import pytest

from sqlalchemy.orm import Session

from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models import *
from asset_manager.repositories.label_mapping_repo import (
    LabelMappingAssetRepository,
    LabelMappingUserRepository,
)
from tests.data.model_creators import create_asset, create_label, create_user
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


class TestLabelMappingAssetRepository:
    """Test suite for LabelMappingAssetRepository"""

    def test_create_and_get_label_mapping_asset(self, db_session: Session):
        """Test creating and retrieving a label mapping for an asset"""
        asset_repo = LabelMappingAssetRepository(db_session)
        create_asset(db_session, id=1)
        create_label(db_session, id=10)

        mapping = asset_repo.create({"item_id": 1, "label_id": 10})

        found = asset_repo.get_by_asset_and_label(asset_id=1, label_id=10)
        assert found is not None
        assert found.id == mapping.id
        assert found.item_id == 1
        assert found.label_id == 10

    def test_get_by_asset_and_label_returns_none_when_not_found(
        self, db_session: Session
    ):
        """Ensure None is returned when no label mapping exists for the given asset/label pair"""
        asset_repo = LabelMappingAssetRepository(db_session)
        result = asset_repo.get_by_asset_and_label(asset_id=999, label_id=888)
        assert result is None


class TestLabelMappingUserRepository:
    """Test suite for LabelMappingUserRepository"""

    def test_create_and_get_label_mapping_user(self, db_session: Session):
        """Test creation and retrieval of a user-label mapping"""
        user_repo = LabelMappingUserRepository(db_session)
        create_user(db_session, id=2)
        create_label(db_session, id=20)

        mapping = user_repo.create({"item_id": 2, "label_id": 20})

        found = user_repo.get_by_user_and_label(user_id=2, label_id=20)
        assert found is not None
        assert found.id == mapping.id
        assert found.item_id == 2
        assert found.label_id == 20

    def test_get_by_user_and_label_returns_none_when_not_found(
        self, db_session: Session
    ):
        """Ensure None is returned when no label mapping exists for the given user/label pair"""
        user_repo = LabelMappingUserRepository(db_session)
        result = user_repo.get_by_user_and_label(user_id=123, label_id=456)
        assert result is None
