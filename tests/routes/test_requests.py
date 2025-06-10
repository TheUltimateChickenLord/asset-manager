from typing import Any
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from asset_manager import main
from asset_manager.db import session
from asset_manager.db.base import Base
from tests.data import auth, seed
from tests.data.model_creators import (
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


class TestRequestManagement:
    """Test class for managing request-related routes in the FastAPI application"""

    def test_get_my_requests(self, db_session: Session):
        """Test retrieving all requests submitted by the logged-in user"""
        user = create_user(db_session)
        for _ in range(5):
            create_request(db_session, user_id=user.id, asset_id=1)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/requests/my", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_submit_request_success(self, db_session: Session):
        """Test submitting a request with proper permissions and valid asset"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="RequestAsset", scope="*")

        token = auth.authenticate_user(user)
        request_data: dict[str, Any] = {"asset_id": 1, "justification": ""}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/requests/", json=request_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["asset_id"] == 1
        assert data["status"] == "Pending"

    def test_submit_request_asset_not_found(self, db_session: Session):
        """Test submitting a request for a non-existent asset"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="RequestAsset", scope="*")

        token = auth.authenticate_user(user)
        request_data: dict[str, Any] = {"asset_id": 999, "justification": ""}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/requests/", json=request_data, headers=headers)

        assert response.status_code == 404

    def test_submit_request_permission_denied(self, db_session: Session):
        """Test submitting a request without the required role"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="RequestAsset", scope="department:HR"
        )

        token = auth.authenticate_user(user)
        request_data: dict[str, Any] = {"asset_id": 1, "justification": ""}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/requests/", json=request_data, headers=headers)

        assert response.status_code == 403

    @pytest.mark.parametrize(
        "status, final_status", [("approve", "Approved"), ("reject", "Rejected")]
    )
    def test_sign_request_success(
        self, db_session: Session, status: str, final_status: str
    ):
        """Test successfully approving a pending request"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")
        request = create_request(db_session, user_id=user.id, asset_id=1)

        token = auth.authenticate_user(user)
        request_data = {"id": request.id}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/requests/{status}", json=request_data, headers=headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == final_status

    @pytest.mark.parametrize("status", ["approve", "reject"])
    def test_sign_request_already_handled(self, db_session: Session, status: str):
        """Test trying to approve a request that is not pending"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")
        request = create_request(
            db_session, user_id=user.id, asset_id=1, status="Approved"
        )

        token = auth.authenticate_user(user)
        request_data = {"id": request.id}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/requests/{status}", json=request_data, headers=headers
        )

        assert response.status_code == 409

    @pytest.mark.parametrize("status", ["approve", "reject"])
    def test_sign_request_not_found(self, db_session: Session, status: str):
        """Test trying to approve a request that is not pending"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")

        token = auth.authenticate_user(user)
        request_data = {"id": 999}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/requests/{status}", json=request_data, headers=headers
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("status", ["approve", "reject"])
    def test_sign_request_no_access(self, db_session: Session, status: str):
        """Test trying to approve a request that is not pending"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="CheckInOutAsset", scope="department:HR"
        )
        request = create_request(db_session, user_id=user.id, asset_id=1)

        token = auth.authenticate_user(user)
        request_data = {"id": request.id}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/requests/{status}", json=request_data, headers=headers
        )

        assert response.status_code == 403

    def test_get_request_by_id_success_scope(self, db_session: Session):
        """Test fetching a request by ID as the request owner"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CheckInOutAsset", scope="*")
        request = create_request(db_session, user_id=1, asset_id=1)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/requests/{request.id}", headers=headers)

        assert response.status_code == 200

    def test_get_request_by_id_success_creator(self, db_session: Session):
        """Test fetching a request by ID as the request owner"""
        user = create_user(db_session)
        request = create_request(db_session, user_id=user.id, asset_id=1)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/requests/{request.id}", headers=headers)

        assert response.status_code == 200

    def test_get_request_by_id_permission_denied(self, db_session: Session):
        """Test fetching a request by ID as a user who lacks permission"""
        user = create_user(db_session)
        request = create_request(db_session, user_id=1, asset_id=1)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/requests/{request.id}", headers=headers)

        assert response.status_code == 403
