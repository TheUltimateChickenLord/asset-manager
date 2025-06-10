import pytest

from sqlalchemy.orm import Session

from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models import *
from asset_manager.repositories.asset_repo import AssetRepository
from tests.data.model_creators import create_asset
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


class TestAssetRepository:
    def test_get_by_status_filters_correctly(self, db_session: Session):
        asset_repo = AssetRepository(db_session)
        create_asset(db_session, status="Available")
        create_asset(db_session, status="In Use")
        results = asset_repo.get_by_status("Available")
        assert len(results) == 1
        assert results[0].status == "Available"

    def test_get_by_status_excludes_deleted(self, db_session: Session):
        asset_repo = AssetRepository(db_session)
        create_asset(db_session, status="Maintenance", is_deleted=True)
        results = asset_repo.get_by_status("Maintenance")
        assert len(results) == 0

    def test_get_by_status_includes_deleted(self, db_session: Session):
        asset_repo = AssetRepository(db_session)
        create_asset(db_session, status="Maintenance", is_deleted=True)
        results = asset_repo.get_by_status("Maintenance", include_deleted=True)
        assert len(results) == 1

    def test_get_due_for_maintenance_filters_correctly(self, db_session: Session):
        asset_repo = AssetRepository(db_session)
        create_asset(db_session, maintenance_rate=28)
        create_asset(db_session, maintenance_rate=29)
        create_asset(db_session, maintenance_rate=30)
        create_asset(db_session, maintenance_rate=31)
        results = asset_repo.get_due_for_maintenance()
        assert len(results) == 3
