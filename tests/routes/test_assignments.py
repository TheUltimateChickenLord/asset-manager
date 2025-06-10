from datetime import date, datetime, timedelta
from typing import Any
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from asset_manager import main
from asset_manager.db import session
from asset_manager.db.base import Base
from tests.data import auth, seed
from tests.data.db_monitor import count_elements_in_db
from tests.data.model_creators import (
    create_asset,
    create_assignment,
    create_request,
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


class TestAssignmentManagement:
    """Test class for managing assignment-related routes in the FastAPI application"""

    def test_check_in_out_assets(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session)

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_id": asset.id,
            "user_id": 1,
            "due_in_days": 10,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assignments/check-out", json=asset_data, headers=headers
        )

        assert response.status_code == 200
        assert (initial_count + 1) == count_elements_in_db(db_session)

        response = client.get(f"/api/assets/{asset.id}", headers=headers)

        assert response.status_code == 200
        assert response.json()["status"] == "In Use"

        asset_data: dict[str, Any] = {
            "asset_id": asset.id,
        }
        response = client.post(
            f"/api/assignments/check-in", json=asset_data, headers=headers
        )

        assert response.status_code == 200
        assert (initial_count + 1) == count_elements_in_db(db_session)

    def test_check_in_out_assets_special(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session, status="Reserved")
        request = create_request(db_session, asset_id=asset.id, user_id=1)

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "due_in_days": 10,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assignments/check-out/{request.id}", json=asset_data, headers=headers
        )

        assert response.status_code == 200
        assert response.json()["user_id"] == 1
        assert (initial_count + 1) == count_elements_in_db(db_session)

        assignment_id = response.json()["id"]

        response = client.get(f"/api/assets/{asset.id}", headers=headers)

        assert response.status_code == 200
        assert response.json()["status"] == "In Use"

        response = client.post(
            f"/api/assignments/check-in/{assignment_id}", headers=headers
        )

        assert response.status_code == 200
        assert (initial_count + 1) == count_elements_in_db(db_session)

    def test_check_out_no_request(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "due_in_days": 10,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assignments/check-out/999", json=asset_data, headers=headers
        )

        assert response.status_code == 404

    def test_check_out_not_available(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session, status="In Use")
        request = create_request(db_session, asset_id=asset.id, user_id=1)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "due_in_days": 10,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assignments/check-out/{request.id}", json=asset_data, headers=headers
        )

        assert response.status_code == 409

        asset_data: dict[str, Any] = {
            "asset_id": asset.id,
            "user_id": 1,
            "due_in_days": 10,
        }
        response = client.post(
            f"/api/assignments/check-out", json=asset_data, headers=headers
        )

        assert response.status_code == 409

    def test_check_out_invalid_scope(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="CheckInOutAsset", scope="department:HR"
        )

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_id": 4,
            "user_id": 1,
            "due_in_days": 10,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assignments/check-out", json=asset_data, headers=headers
        )

        assert response.status_code == 403

    def test_check_in_not_in_use(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session)
        assignment = create_assignment(db_session, asset_id=asset.id)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_id": asset.id,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assignments/check-in", json=asset_data, headers=headers
        )

        assert response.status_code == 409

        response = client.post(f"/api/assignments/check-in/999", headers=headers)

        assert response.status_code == 409

        response = client.post(
            f"/api/assignments/check-in/{assignment.id}", headers=headers
        )

        assert response.status_code == 409

    def test_check_in_invalid_scope(self, db_session: Session) -> None:
        """Test checking in and out assets"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="CheckInOutAsset", scope="department:HR"
        )

        assignment = create_assignment(db_session, asset_id=4)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assignments/check-in/{assignment.id}", headers=headers
        )

        assert response.status_code == 403

    def test_no_assignments(self, db_session: Session):
        """Test a user with no assignments"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/assignments/my", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_many_assignments(self, db_session: Session):
        """Test a user with many assignments"""
        user = create_user(db_session)

        create_assignment(db_session, asset_id=2, user_id=user.id)
        create_assignment(db_session, asset_id=3, assigned_by_id=user.id)
        create_assignment(
            db_session, asset_id=4, user_id=user.id, assigned_by_id=user.id
        )

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/assignments/my", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_request_return_assets(self, db_session: Session) -> None:
        """Test requesting the return of assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session)
        assignment = create_assignment(
            db_session, asset_id=asset.id, due_date=(date.today() + timedelta(days=10))
        )

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_assignment_id": assignment.id,
            "due_in_days": 0,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(
            f"/api/assignments/request-return", json=asset_data, headers=headers
        )

        assert response.status_code == 200
        assert response.json()["due_date"] == date.today().isoformat()

    def test_request_return_assets_negative_time(self, db_session: Session) -> None:
        """Test requesting the return of assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        asset = create_asset(db_session)
        assignment = create_assignment(db_session, asset_id=asset.id)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_assignment_id": assignment.id,
            "due_in_days": -10,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(
            f"/api/assignments/request-return", json=asset_data, headers=headers
        )

        assert response.status_code == 422

    def test_overdue_assignments(self, db_session: Session) -> None:
        """Test that overdue assignments are returned"""
        user = create_user(db_session)

        create_assignment(
            db_session,
            asset_id=2,
            user_id=user.id,
            due_date=date.today(),
            returned_at=datetime.now(),
        )
        create_assignment(
            db_session,
            asset_id=2,
            user_id=user.id,
            due_date=(date.today() - timedelta(days=1)),
            returned_at=datetime.now(),
        )
        create_assignment(
            db_session,
            asset_id=2,
            user_id=user.id,
            due_date=(date.today() - timedelta(days=1)),
        )
        create_assignment(
            db_session, asset_id=3, assigned_by_id=user.id, due_date=date.today()
        )
        create_assignment(
            db_session,
            asset_id=4,
            user_id=user.id,
            assigned_by_id=user.id,
            due_date=date.today(),
        )

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/assignments/overdue", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_overdue_assignments_extra_days(self, db_session: Session) -> None:
        """Test that overdue assignments are returned"""
        user = create_user(db_session)

        create_assignment(
            db_session,
            asset_id=4,
            user_id=user.id,
            assigned_by_id=user.id,
            due_date=(date.today() + timedelta(days=2)),
        )

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/assignments/overdue?due_in_days=3", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_assignment_by_id_success(self, db_session: Session):
        """Should return another user's data if ReadUser role matches"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="*")

        assignment = create_assignment(
            db_session,
            asset_id=4,
            user_id=user.id,
            assigned_by_id=user.id,
            due_date=(date.today() + timedelta(days=2)),
        )

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/assignments/{assignment.id}", headers=headers)

        assert response.status_code == 200

    def test_get_assignment_by_id_forbidden(self, db_session: Session):
        """Should forbid access without proper role"""
        user = create_user(db_session)

        assignment = create_assignment(
            db_session,
            asset_id=4,
            user_id=1,
            assigned_by_id=1,
            due_date=(date.today() + timedelta(days=2)),
        )

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/assignments/{assignment.id}", headers=headers)

        assert response.status_code == 403

    def test_get_assignment_not_found(self, db_session: Session):
        """Should return 404 for non-existent user"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadUser", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/assignments/999", headers=headers)

        assert response.status_code == 404
