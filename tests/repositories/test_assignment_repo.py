from datetime import datetime, timedelta, date

import pytest

from sqlalchemy.orm import Session

from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models import *
from asset_manager.repositories.assignment_repo import AssetAssignmentRepository
from tests.data.model_creators import create_asset, create_user
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


class TestAssetAssignmentRepository:
    def test_check_out_asset_creates_assignment(self, db_session: Session):
        repo = AssetAssignmentRepository(db_session)
        asset = create_asset(db_session)
        create_user(db_session, id=1)
        create_user(db_session, id=2)
        assignment = repo.check_out_asset(
            asset, user_id=1, assigned_by_id=2, due_in_days=5
        )
        assert assignment.asset_id == asset.id
        assert assignment.user_id == 1
        assert assignment.assigned_by_id == 2
        assert assignment.due_date == date.today() + timedelta(days=5)

    def test_get_asset_assignment_returns_unreturned_only(self, db_session: Session):
        repo = AssetAssignmentRepository(db_session)
        asset = create_asset(db_session)
        create_user(db_session, id=1)
        assignment = repo.check_out_asset(
            asset, user_id=1, assigned_by_id=1, due_in_days=3
        )

        # Should return assignment
        found = repo.get_asset_assignment(asset_id=asset.id)
        assert found is not None
        assert found.id == assignment.id

        # Mark returned
        assignment.returned_at = datetime.now()
        db_session.commit()

        # Should now return None
        found = repo.get_asset_assignment(asset_id=asset.id)
        assert found is None

    def test_get_by_user_finds_assignments(self, db_session: Session):
        repo = AssetAssignmentRepository(db_session)
        asset = create_asset(db_session)
        create_user(db_session, id=1)
        create_user(db_session, id=2)

        repo.check_out_asset(asset, user_id=1, assigned_by_id=2, due_in_days=3)
        results = repo.get_by_user(1)
        assert len(results) == 1

        results = repo.get_by_user(2)
        assert len(results) == 1

    def test_get_overdue_filters_by_date_and_user(self, db_session: Session):
        repo = AssetAssignmentRepository(db_session)
        asset = create_asset(db_session)
        create_user(db_session, id=3)
        create_user(db_session, id=4)

        overdue_assignment = repo.check_out_asset(
            asset, user_id=3, assigned_by_id=4, due_in_days=-5
        )
        db_session.commit()

        upcoming_assignment = repo.check_out_asset(
            asset, user_id=3, assigned_by_id=4, due_in_days=5
        )
        db_session.commit()

        results = repo.get_overdue(user_id=3, due_in_days=0)
        assert any(a.id == overdue_assignment.id for a in results)
        assert all(a.due_date <= date.today() for a in results)

        # Should exclude future assignments
        assert all(a.id != upcoming_assignment.id for a in results)
