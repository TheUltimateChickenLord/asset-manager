from typing import Any
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


class TestUserManagement:
    """Test class for managing user-related routes in the FastAPI application"""

    def test_get_users_as_admin(self, db_session: Session):
        """Admin with global ReadUser scope should get all users"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == 11

    def test_get_users_as_limited_user(self, db_session: Session):
        """User with limited ReadUser scope should get filtered users"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="department:HR")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_get_users_denied_no_scope(self, db_session: Session):
        """User with no ReadUser roles should get 403"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/", headers=headers)

        assert response.status_code == 403

    def test_get_myself(self, db_session: Session):
        """Should return the authenticated user's own details"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert user.id == data["id"]
        assert user.name == data["name"]
        assert user.email == data["email"]

    def test_get_user_by_id_success(self, db_session: Session):
        """Should return another user's data if ReadUser role matches"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/1", headers=headers)

        assert response.status_code == 200

    def test_get_user_by_id_forbidden(self, db_session: Session):
        """Should forbid access without proper role"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/1", headers=headers)

        assert response.status_code == 403

    def test_get_user_by_id_self(self, db_session: Session):
        """Should return own user data even without ReadUser role"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/users/{user.id}", headers=headers)

        assert response.status_code == 200

    def test_get_user_not_found(self, db_session: Session):
        """Should return 404 for non-existent user"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/999", headers=headers)

        assert response.status_code == 404

    def test_create_user_success(self, db_session: Session):
        """Should create a user when caller has proper role"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")

        token = auth.authenticate_user(user)
        user_data: dict[str, Any] = {
            "name": "test_user",
            "email": "test_user@example.com",
            "password": "Password123!",
            "labels": ["department:HR"],
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/users", json=user_data, headers=headers)

        assert response.status_code == 200

    def test_create_user_missing_label(self, db_session: Session):
        """Should reject user creation without labels"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")

        token = auth.authenticate_user(user)
        user_data: dict[str, Any] = {
            "name": "test_user",
            "email": "test_user@example.com",
            "password": "Password123!",
            "labels": [],
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/users", json=user_data, headers=headers)

        assert response.status_code == 400

    def test_create_user_forbidden(self, db_session: Session):
        """Should reject user creation if creator lacks proper label access"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="CreateEditUser", scope="department:IT"
        )
        create_role(
            db_session, user_id=user.id, role="CreateEditUser", scope="location:Lon"
        )

        token = auth.authenticate_user(user)
        user_data: dict[str, Any] = {
            "name": "test_user",
            "email": "test_user@example.com",
            "password": "Password123!",
            "labels": ["department:HR", "location:Lon"],
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/users", json=user_data, headers=headers)

        assert response.status_code == 403

    def test_create_user_duplicate_email(self, db_session: Session):
        """Should reject duplicate email"""
        user = create_user(db_session)
        create_user(db_session, email="usedemail@example.com")
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")

        token = auth.authenticate_user(user)
        user_data: dict[str, Any] = {
            "name": "test_user",
            "email": "usedemail@example.com",
            "password": "Password123!",
            "labels": ["department:HR"],
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/users", json=user_data, headers=headers)

        assert response.status_code == 400

    def test_create_user_duplicate_name(self, db_session: Session):
        """Should reject duplicate name"""
        user = create_user(db_session)
        create_user(db_session, name="usedname")
        create_role(db_session, user_id=user.id, role="CreateEditUser", scope="*")

        token = auth.authenticate_user(user)
        user_data: dict[str, Any] = {
            "name": "usedname",
            "email": "test_user@example.com",
            "password": "Password123!",
            "labels": ["department:HR"],
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/users", json=user_data, headers=headers)

        assert response.status_code == 400

    def test_soft_delete_user(self, db_session: Session):
        """Should soft delete user"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="DeleteUser", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"/api/users/{test_user.id}", headers=headers)

        assert response.status_code == 200
        db_session.refresh(test_user)
        assert test_user.is_deleted

    def test_soft_delete_self(self, db_session: Session):
        """Should deny delete if not user is self"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="DeleteUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"/api/users/{user.id}", headers=headers)

        assert response.status_code == 403

    def test_soft_delete_user_not_found(self, db_session: Session):
        """Should deny soft delete if user not found"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="DeleteUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete("/api/users/999", headers=headers)

        assert response.status_code == 404

    def test_soft_delete_user_not_allowed(self, db_session: Session):
        """Should deny soft delete if user not allowed"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"/api/users/1", headers=headers)

        assert response.status_code == 403

    def test_disable_user(self, db_session: Session):
        """Should disable user"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="DisableUser", scope="*")
        test_user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(
            f"/api/users/{test_user.id}?temp=true", headers=headers
        )

        assert response.status_code == 200
        db_session.refresh(test_user)
        assert test_user.is_disabled

    def test_disable_self(self, db_session: Session):
        """Should deny disable if not user is self"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="DisableUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"/api/users/{user.id}?temp=true", headers=headers)

        assert response.status_code == 403

    def test_disable_user_not_found(self, db_session: Session):
        """Should deny disable if user not found"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="DisableUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"/api/users/999?temp=true", headers=headers)

        assert response.status_code == 404

    def test_disable_user_not_allowed(self, db_session: Session):
        """Should deny disable if user not allowed"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"/api/users/1?temp=true", headers=headers)

        assert response.status_code == 403

    def test_enable_user(self, db_session: Session):
        """Should enable user"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="DisableUser", scope="*")
        test_user = create_user(db_session, is_disabled=True)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(f"/api/users/{test_user.id}", headers=headers)

        assert response.status_code == 200
        db_session.refresh(test_user)
        assert test_user.is_disabled is False

    def test_enable_self(self, db_session: Session):
        """Should deny enable if not user is self"""
        user = create_user(db_session, is_disabled=True)
        create_role(db_session, user_id=user.id, role="DisableUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(f"/api/users/{user.id}", headers=headers)

        assert response.status_code == 401

    def test_enable_user_not_found(self, db_session: Session):
        """Should deny enable if user not found"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="DisableUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(f"/api/users/999", headers=headers)

        assert response.status_code == 404

    def test_enable_user_not_allowed(self, db_session: Session):
        """Should deny enable if user not allowed"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(f"/api/users/1", headers=headers)

        assert response.status_code == 403
