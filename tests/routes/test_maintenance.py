import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from asset_manager import main
from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models.label_mapping import LabelMappingAsset
from tests.data import auth, seed
from tests.data.model_creators import (
    create_asset,
    create_label,
    create_role,
    create_user,
)
from tests.data.reload import reload_all_modules


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch: pytest.MonkeyPatch):
    """Fixture to set the database to an in-memory SQLite database for testing"""
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./tests/data/test.db")
    monkeypatch.setenv("SECRET_KEY", "testsecret")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1")
    monkeypatch.setenv("LOG_DIR", "tests/logs")
    reload_all_modules()


@pytest.fixture(scope="function")
def db_session():
    """Fixture to create a new database session for testing"""
    current_session = session.SessionLocal()
    seed.delete_all(current_session)
    seed.create_all(current_session)
    yield current_session
    current_session.close()
    Base.metadata.drop_all(bind=session.engine)


class TestMaintenanceManagement:
    """Test class for managing maintenance-related routes in the FastAPI application"""

    def test_check_in_out_assets(self, db_session: Session) -> None:
        """Test checking in and out assets for maintenance"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session)

        token = auth.authenticate_user(user)
        asset_data = {"asset_id": asset.id}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/maintenance/check-out", json=asset_data, headers=headers
        )

        assert response.status_code == 200

        db_session.refresh(asset)

        assert asset.status == "Maintenance"

        asset_data = {"asset_id": asset.id}
        response = client.post(
            f"/api/maintenance/check-in", json=asset_data, headers=headers
        )

        assert response.status_code == 200

        db_session.refresh(asset)

        assert asset.status == "Available"

    def test_check_out_not_available(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session, status="In Use")

        token = auth.authenticate_user(user)
        asset_data = {"asset_id": asset.id}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/maintenance/check-out", json=asset_data, headers=headers
        )

        assert response.status_code == 409

    def test_check_out_invalid_scope(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="CheckInOutAsset", scope="department:HR"
        )

        asset = create_asset(db_session, status="Available")
        label = create_label(db_session)
        db_session.add(LabelMappingAsset(item_id=asset.id, label_id=label.id))
        db_session.commit()

        token = auth.authenticate_user(user)
        asset_data = {"asset_id": asset.id}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/maintenance/check-out", json=asset_data, headers=headers
        )

        assert response.status_code == 403

    def test_check_in_not_in_use(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session)

        token = auth.authenticate_user(user)
        asset_data = {"asset_id": asset.id}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/maintenance/check-in", json=asset_data, headers=headers
        )

        assert response.status_code == 409

    def test_check_in_invalid_scope(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="CheckInOutAsset", scope="department:HR"
        )

        asset = create_asset(db_session, status="Maintenance")
        label = create_label(db_session)
        db_session.add(LabelMappingAsset(item_id=asset.id, label_id=label.id))
        db_session.commit()

        token = auth.authenticate_user(user)
        asset_data = {"asset_id": asset.id}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/maintenance/check-in", json=asset_data, headers=headers
        )

        assert response.status_code == 403
