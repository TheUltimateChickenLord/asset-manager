import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from asset_manager import main
from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models.label_mapping import LabelMappingAsset, LabelMappingUser
from tests.data import auth, seed
from tests.data.model_creators import (
    create_asset,
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


class TestLabelManagement:
    """Test class for managing assignment-related routes in the FastAPI application"""

    def test_get_labels_success(self, db_session: Session):
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/labels/", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == 4

    def test_create_label_success(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")

        token = auth.authenticate_user(user)
        label_data = {"name": "department:Finance"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/labels/", json=label_data, headers=headers)

        assert response.status_code == 200
        assert response.json()["name"] == "department:Finance"

    def test_create_label_invalid_permissions(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")

        token = auth.authenticate_user(user)
        label_data = {"name": "department:IT"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/labels/", json=label_data, headers=headers)

        assert response.status_code == 200
        assert response.json()["name"] == "department:IT"

    def test_create_label_integrity_error(self, db_session: Session):
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="CreateEditAsset", scope="department:HR"
        )

        token = auth.authenticate_user(user)
        label_data = {"name": "department:IT"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/labels/", json=label_data, headers=headers)

        assert response.status_code == 403

    def test_assign_label_to_user_permission_denied(self, db_session: Session):
        user = create_user(db_session)
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        label_data = {"label_id": 1}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/labels/assign/user/{test_user.id}", json=label_data, headers=headers
        )

        assert response.status_code == 403

    def test_assign_label_to_user_user_not_found(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")

        token = auth.authenticate_user(user)
        label_data = {"label_id": 1}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/labels/assign/user/999", json=label_data, headers=headers
        )

        assert response.status_code == 404

    def test_assign_label_to_user_label_not_found(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        label_data = {"label_id": 999}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/labels/assign/user/{test_user.id}", json=label_data, headers=headers
        )

        assert response.status_code == 404

    def test_assign_label_to_user(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        label_data = {"label_id": 1}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/labels/assign/user/{test_user.id}", json=label_data, headers=headers
        )

        assert response.status_code == 200
        db_session.refresh(test_user)
        assert len(test_user.labels) == 1
        assert test_user.labels[0].id == 1

    def test_assign_label_to_asset_permission_denied(self, db_session: Session):
        user = create_user(db_session)
        test_asset = create_asset(db_session)

        token = auth.authenticate_user(user)
        label_data = {"label_id": 1}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/labels/assign/asset/{test_asset.id}",
            json=label_data,
            headers=headers,
        )

        assert response.status_code == 403

    def test_assign_label_to_asset_asset_not_found(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")

        token = auth.authenticate_user(user)
        label_data = {"label_id": 1}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/labels/assign/asset/999", json=label_data, headers=headers
        )

        assert response.status_code == 404

    def test_assign_label_to_asset_label_not_found(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")
        test_asset = create_asset(db_session)

        token = auth.authenticate_user(user)
        label_data = {"label_id": 999}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/labels/assign/asset/{test_asset.id}",
            json=label_data,
            headers=headers,
        )

        assert response.status_code == 404

    def test_assign_label_to_asset(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")
        test_asset = create_asset(db_session)

        token = auth.authenticate_user(user)
        label_data = {"label_id": 1}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/labels/assign/asset/{test_asset.id}",
            json=label_data,
            headers=headers,
        )

        assert response.status_code == 200
        db_session.refresh(test_asset)
        assert len(test_asset.labels) == 1
        assert test_asset.labels[0].id == 1

    def test_unassign_label_from_user_permission_denied(self, db_session: Session):
        user = create_user(db_session)
        test_user = create_user(db_session)
        db_session.add(LabelMappingUser(item_id=test_user.id, label_id=1))
        db_session.commit()

        db_session.refresh(test_user)
        assert len(test_user.labels) == 1

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/labels/assign/user/{test_user.id}?label_id=1", headers=headers
        )

        assert response.status_code == 403
        db_session.refresh(test_user)
        assert len(test_user.labels) == 1

    def test_unassign_label_from_user_user_not_found(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/labels/assign/user/999?label_id=1", headers=headers
        )

        assert response.status_code == 404

    def test_unassign_label_from_user_label_not_found(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/labels/assign/user/{test_user.id}?label_id=999", headers=headers
        )

        assert response.status_code == 404

    def test_unassign_label_from_user(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        test_user = create_user(db_session)
        db_session.add(LabelMappingUser(item_id=test_user.id, label_id=1))
        db_session.commit()

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/labels/assign/user/{test_user.id}?label_id=1", headers=headers
        )

        assert response.status_code == 200
        db_session.refresh(test_user)
        assert len(test_user.labels) == 0

    def test_unassign_label_from_asset_permission_denied(self, db_session: Session):
        user = create_user(db_session)
        test_asset = create_asset(db_session)
        db_session.add(LabelMappingAsset(item_id=test_asset.id, label_id=1))
        db_session.commit()

        db_session.refresh(test_asset)
        assert len(test_asset.labels) == 1

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/labels/assign/asset/{test_asset.id}?label_id=1", headers=headers
        )

        assert response.status_code == 403
        db_session.refresh(test_asset)
        assert len(test_asset.labels) == 1

    def test_unassign_label_from_asset_user_not_found(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/labels/assign/asset/999?label_id=1", headers=headers
        )

        assert response.status_code == 404

    def test_unassign_label_from_asset_label_not_found(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        test_asset = create_asset(db_session)
        db_session.add(LabelMappingAsset(item_id=test_asset.id, label_id=1))
        db_session.commit()

        db_session.refresh(test_asset)
        assert len(test_asset.labels) == 1

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/labels/assign/asset/{test_asset.id}?label_id=999", headers=headers
        )

        assert response.status_code == 404
        db_session.refresh(test_asset)
        assert len(test_asset.labels) == 1

    def test_unassign_label_from_asset(self, db_session: Session):
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")
        test_asset = create_asset(db_session)
        db_session.add(LabelMappingAsset(item_id=test_asset.id, label_id=1))
        db_session.commit()

        db_session.refresh(test_asset)
        assert len(test_asset.labels) == 1

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/labels/assign/asset/{test_asset.id}?label_id=1", headers=headers
        )

        assert response.status_code == 200
        db_session.refresh(test_asset)
        assert len(test_asset.labels) == 0

    def test_get_valid_label(self, db_session: Session):
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/labels/1", headers=headers)

        assert response.status_code == 200

    def test_get_invalid_label(self, db_session: Session):
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/labels/999", headers=headers)

        assert response.status_code == 404
