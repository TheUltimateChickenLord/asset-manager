import pytest
from sqlalchemy.orm import Session

from asset_manager.db.base import Base
from asset_manager.db import session
from asset_manager.db.models import *
from tests.data.reload import reload_all_modules
from tests.data.repositories import DummyHardRepo, DummySoftRepo


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


class TestAbstractCRUDRepoSoftDelete:
    def test_create_and_get(self, db_session: Session):
        repo = DummySoftRepo(db_session)
        item = repo.create({"name": "TestItem"})
        assert item.id is not None
        result = repo.get_by_id(item.id)
        assert result is not None
        assert result.name == "TestItem"

    def test_get_all_excludes_deleted(self, db_session: Session):
        repo = DummySoftRepo(db_session)
        repo.create({"name": "Active"})
        repo.create({"name": "Deleted", "is_deleted": True})
        all_items = repo.get_all()
        assert len(all_items) == 1
        assert all_items[0].name == "Active"

    def test_soft_delete_marks_item(self, db_session: Session):
        repo = DummySoftRepo(db_session)
        item = repo.create({"name": "Deletable"})
        deleted_item = repo.delete(item)
        assert deleted_item.is_deleted
        assert repo.get_by_id(item.id) is not None
        assert repo.get_by_id(item.id, include_deleted=False) is None

    def test_update_item(self, db_session: Session):
        repo = DummySoftRepo(db_session)
        item = repo.create({"name": "Before"})
        updated = repo.update(item, {"name": "After"})
        result = repo.get_by_id(item.id)
        assert result is not None
        assert result.name == "After"
        assert updated.name == "After"


class TestAbstractCRUDRepoHardDelete:
    def test_create_and_get(self, db_session: Session):
        repo = DummyHardRepo(db_session)
        item = repo.create({"name": "Item"})
        result = repo.get_by_id(item.id)
        assert result is not None
        assert result.name == "Item"

    def test_get_all_includes_all(self, db_session: Session):
        repo = DummyHardRepo(db_session)
        repo.create({"name": "A"})
        repo.create({"name": "B"})
        all_items = repo.get_all()
        assert len(all_items) == 2

    def test_delete_removes_item(self, db_session: Session):
        repo = DummyHardRepo(db_session)
        item = repo.create({"name": "ToDelete"})
        repo.delete(item)
        assert repo.get_by_id(item.id) is None
