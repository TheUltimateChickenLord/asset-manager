import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from asset_manager import main
from asset_manager.db import session
from asset_manager.db.base import Base
from tests.data import auth, seed
from tests.data.model_creators import (
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


class TestRoleRoutes:
    """Test class for managing role-related routes in the FastAPI application"""

    def test_get_roles_for_user_success(self, db_session: Session):
        """Should return the roles for a user if current user has permission"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/roles/user/1", headers=headers)

        assert response.status_code == 200

    def test_get_roles_for_user_self(self, db_session: Session):
        """User should be able to view their own roles"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/roles/user/{user.id}", headers=headers)

        assert response.status_code == 200

    def test_get_roles_for_user_not_found(self, db_session: Session):
        """Should return the roles for a user if current user has permission"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/roles/user/999", headers=headers)

        assert response.status_code == 404

    def test_get_roles_for_user_unauthorized(self, db_session: Session):
        """Should block access to another user's roles if permissions are missing"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="department:HR")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/roles/user/1", headers=headers)

        assert response.status_code == 403

    def test_assign_role_success_all(self, db_session: Session):
        """Should assign a valid role if current user has permission"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "*"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/roles/user/{test_user.id}", json=role_data, headers=headers
        )

        assert response.status_code == 200

    def test_assign_role_success_one(self, db_session: Session):
        """Should assign a valid role if current user has permission"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "department:HR"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/roles/user/{test_user.id}", json=role_data, headers=headers
        )

        assert response.status_code == 200

    def test_assign_invalid_role_user_not_found(self, db_session: Session):
        """Should assign a valid role if current user has permission"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "*"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(f"/api/roles/user/999", json=role_data, headers=headers)

        assert response.status_code == 404

    def test_assign_role_invalid_role(self, db_session: Session):
        """Should return 404 if role is not in the list of allowed roles"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        role_data = {"role": "InvalidRole", "scope": "*"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/roles/user/{test_user.id}", json=role_data, headers=headers
        )

        assert response.status_code == 404

    def test_assign_role_invalid_scope(self, db_session: Session):
        """Should return 404 if scope is not in the list of labels"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "Invalid Scope"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/roles/user/{test_user.id}", json=role_data, headers=headers
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("scope", ["*", "department:IT"])
    def test_assign_role_permission_denied(self, db_session: Session, scope: str):
        """Should block role assignment without permission"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        create_role(
            db_session, user_id=user.id, role="ReadAsset", scope="department:HR"
        )
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": scope}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/roles/user/{test_user.id}", json=role_data, headers=headers
        )

        assert response.status_code == 403

    def test_delete_role_success(self, db_session: Session):
        """Should successfully delete a user role"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        test_user = create_user(db_session)
        create_role(db_session, user_id=test_user.id, role="ReadAsset", scope="*")

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "*"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/roles/user/{test_user.id}", params=role_data, headers=headers
        )

        assert response.status_code == 200
        db_session.refresh(test_user)
        assert len(test_user.roles) == 0

    def test_delete_role_not_found(self, db_session: Session):
        """Should return 404 if the role doesn't exist on user"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "*"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/roles/user/{test_user.id}", params=role_data, headers=headers
        )

        assert response.status_code == 404

    def test_delete_role_user_not_found(self, db_session: Session):
        """Should return 404 if the role doesn't exist on user"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "*"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/roles/user/999", params=role_data, headers=headers
        )

        assert response.status_code == 404

    def test_delete_role_permission_denied_create(self, db_session: Session):
        """Should return 403 if user lacks permission to delete role"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        test_user = create_user(db_session)
        create_role(db_session, user_id=test_user.id, role="ReadAsset", scope="*")

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "*"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/roles/user/{test_user.id}", params=role_data, headers=headers
        )

        assert response.status_code == 403
        db_session.refresh(test_user)
        assert len(test_user.roles) == 1

    def test_delete_role_permission_denied_role(self, db_session: Session):
        """Should return 403 if user lacks permission to delete role"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")
        test_user = create_user(db_session)
        create_role(db_session, user_id=test_user.id, role="ReadAsset", scope="*")

        token = auth.authenticate_user(user)
        role_data = {"role": "ReadAsset", "scope": "*"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/roles/user/{test_user.id}", params=role_data, headers=headers
        )

        assert response.status_code == 403
        db_session.refresh(test_user)
        assert len(test_user.roles) == 1
