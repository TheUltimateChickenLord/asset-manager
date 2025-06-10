"""Test module for LabelRepository"""

import pytest

from sqlalchemy.orm import Session

from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models import *
from asset_manager.repositories.label_repo import LabelRepository
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


class TestLabelRepository:
    """Test suite for LabelRepository"""

    def test_create_and_retrieve_label(self, db_session: Session):
        """Verify a label can be created and retrieved by ID"""
        label_repo = LabelRepository(db_session)
        new_label = label_repo.create({"name": "Security"})
        retrieved = label_repo.get_by_id(new_label.id)
        assert retrieved is not None
        assert retrieved.name == "Security"

    def test_has_relationships_returns_false_when_empty(self, db_session: Session):
        """Ensure has_relationships() returns False for unlinked label"""
        label_repo = LabelRepository(db_session)
        label = label_repo.create({"name": "Unlinked"})
        assert not label_repo.has_relationships(label)

    def test_has_relationships_returns_true_for_linked_user(self, db_session: Session):
        """has_relationships() should return True if label has users"""
        label_repo = LabelRepository(db_session)
        user = create_user(db_session)
        label = create_label(db_session)
        user.labels.append(label)
        db_session.commit()
        db_session.refresh(label)
        assert label_repo.has_relationships(label)

    def test_has_relationships_returns_true_for_linked_asset(self, db_session: Session):
        """has_relationships() should return True if label has assets"""
        label_repo = LabelRepository(db_session)
        asset = create_asset(db_session)
        label = create_label(db_session)
        asset.labels.append(label)
        db_session.commit()
        db_session.refresh(label)
        assert label_repo.has_relationships(label)

    def test_get_by_user_returns_linked_labels(self, db_session: Session):
        """get_by_user() should return labels linked to the given user"""
        label_repo = LabelRepository(db_session)
        user = create_user(db_session, id=5)
        label1 = create_label(db_session, name="Hardware")
        create_label(db_session, name="Software")
        user.labels.append(label1)
        db_session.commit()

        results = label_repo.get_by_user(user_id=5)
        assert len(results) == 1
        assert results[0].name == "Hardware"

    def test_get_by_user_returns_empty_if_none_linked(self, db_session: Session):
        """get_by_user() should return an empty list if no labels are linked"""
        label_repo = LabelRepository(db_session)
        create_user(db_session, id=99)
        results = label_repo.get_by_user(user_id=99)
        assert results == []
