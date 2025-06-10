from typing import Any
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from asset_manager import main
from asset_manager.db import session
from asset_manager.db.base import Base
from tests.data import seed, auth
from tests.data.db_monitor import count_elements_in_db
from tests.data.model_creators import create_asset, create_role, create_user
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


class TestAssetManagement:
    """Test class for managing asset-related routes in the FastAPI application"""

    @pytest.mark.parametrize(
        "scopes, labels",
        [
            (["*"], ["department:IT"]),
            (["department:IT"], ["department:IT"]),
            (["department:IT", "department:HR"], ["department:IT"]),
            (["*", "department:HR"], ["department:IT"]),
            (["*"], ["department:IT", "location:Lon"]),
            (["department:IT", "location:Lon"], ["department:IT", "location:Lon"]),
            (
                ["department:IT", "department:HR", "location:Lon"],
                ["department:IT", "location:Lon"],
            ),
            (["*", "department:HR", "location:Lon"], ["department:IT", "location:Lon"]),
        ],
    )
    def test_create_asset_with_role_scope(
        self, db_session: Session, scopes: list[str], labels: list[str]
    ) -> None:
        """Test that asset creation is authorized based on user role and scope"""
        user = create_user(db_session)
        for scope in scopes:
            create_role(
                db_session, user_id=user.id, role="CreateEditAsset", scope=scope
            )

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_tag": "B234",
            "name": "Tablet",
            "description": "A lightweight tablet",
            "purchase_date": "2025-01-01",
            "purchase_cost": 600.0,
            "maintenance_rate": 8,
            "labels": labels,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/assets/", json=asset_data, headers=headers)

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "scopes, labels",
        [
            (["department:IT"], ["department:HR"]),
            (["department:IT", "location:Lon"], ["department:HR"]),
            (["department:IT"], ["department:HR", "location:Man"]),
            (["department:IT", "location:Lon"], ["department:HR", "location:Man"]),
            (["department:HR"], ["department:HR", "location:Man"]),
            (["department:HR", "location:Lon"], ["department:HR", "location:Man"]),
        ],
    )
    def test_create_asset_with_invalid_scope(
        self, db_session: Session, scopes: list[str], labels: list[str]
    ) -> None:
        """Test asset creation with an invalid user role/scope"""
        user = create_user(db_session)
        for scope in scopes:
            create_role(
                db_session, user_id=user.id, role="CreateEditAsset", scope=scope
            )

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_tag": "B234",
            "name": "Tablet",
            "description": "A lightweight tablet",
            "purchase_date": "2025-01-01",
            "purchase_cost": 600.0,
            "maintenance_rate": 8,
            "labels": labels,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/assets/", json=asset_data, headers=headers)

        assert initial_count == count_elements_in_db(db_session)
        assert response.status_code == 403

    def test_create_asset_with_no_labels(self, db_session: Session) -> None:
        """Test that asset creation is authorized based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_tag": "B234",
            "name": "Tablet",
            "description": "A lightweight tablet",
            "purchase_date": "2025-01-01",
            "purchase_cost": 600.0,
            "maintenance_rate": 8,
            "labels": [],
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/assets/", json=asset_data, headers=headers)

        assert initial_count == count_elements_in_db(db_session)
        assert response.status_code == 400

    def test_create_asset_without_required_field(self, db_session: Session) -> None:
        """Test that asset creation is authorized based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_tag": "B234",
            "description": "A lightweight tablet",
            "purchase_date": "2025-01-01",
            "purchase_cost": 600.0,
            "maintenance_rate": 8,
            "labels": ["department:IT"],
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/assets/", json=asset_data, headers=headers)

        assert initial_count == count_elements_in_db(db_session)
        assert response.status_code == 422

    def test_create_asset_with_invalid_label(self, db_session: Session) -> None:
        """Test that asset creation is authorized based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {
            "asset_tag": "B234",
            "name": "Tablet",
            "description": "A lightweight tablet",
            "purchase_date": "2025-01-01",
            "purchase_cost": 600.0,
            "maintenance_rate": 8,
            "labels": ["invalid_label"],
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/assets/", json=asset_data, headers=headers)

        assert initial_count == count_elements_in_db(db_session)
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "scopes, visible",
        [
            (["department:HR"], 4),
            (["*"], 10),
            (["department:IT"], 5),
            (["location:Lon"], 3),
            (["location:Man"], 3),
            (["department:HR", "location:Lon"], 6),
            (["location:Man", "location:Lon"], 3),
            (["department:IT", "location:Lon"], 5),
            (["department:IT", "location:Lon", "location:Man"], 5),
            (["department:HR", "department:IT", "location:Lon"], 10),
            (["*", "department:IT"], 10),
        ],
    )
    def test_get_assets(
        self, db_session: Session, scopes: list[str], visible: int
    ) -> None:
        """Test getting a list of assets based on user role and scope"""
        user = create_user(db_session)
        for scope in scopes:
            create_role(db_session, user_id=user.id, role="ReadAsset", scope=scope)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/assets/", headers=headers)

        assert response.status_code == 200
        assert len(response.json()) == visible

    def test_get_assets_no_scope(self, db_session: Session) -> None:
        """Test getting a list of assets based on user role and scope"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/assets/", headers=headers)

        assert response.status_code == 403

    @pytest.mark.parametrize(
        "scopes, visible",
        [
            (["department:HR"], 0),
            (["*"], 4),
            (["department:IT"], 2),
            (["department:HR", "department:IT"], 3),
            (["department:HR", "department:IT", "location:Lon"], 4),
            (["*", "department:IT"], 4),
        ],
    )
    def test_get_assets_by_status(
        self, db_session: Session, scopes: list[str], visible: int
    ) -> None:
        """Test getting a list of assets based on user role and scope"""
        user = create_user(db_session)
        for scope in scopes:
            create_role(db_session, user_id=user.id, role="ReadAsset", scope=scope)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(
            "/api/assets/status?asset_status=Available", headers=headers
        )

        assert response.status_code == 200
        assert len(response.json()) == visible

    @pytest.mark.parametrize(
        "status",
        ["available", "invalid_status", ""],
    )
    def test_get_assets_by_invalid_status(
        self, db_session: Session, status: str
    ) -> None:
        """Test getting a list of assets based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(
            f"/api/assets/status?asset_status={status}", headers=headers
        )

        assert response.status_code == 422

    @pytest.mark.parametrize(
        "status, visible",
        [("Available", 4), ("In Use", 3), ("Maintenance", 3)],
    )
    def test_get_assets_by_valid_status(
        self, db_session: Session, status: str, visible: int
    ) -> None:
        """Test getting a list of assets based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(
            f"/api/assets/status?asset_status={status}", headers=headers
        )

        assert response.status_code == 200
        assert len(response.json()) == visible

    def test_get_assets_by_status_no_scope(self, db_session: Session) -> None:
        """Test getting a list of assets based on user role and scope"""
        user = create_user(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(
            "/api/assets/status?asset_status=Available", headers=headers
        )

        assert response.status_code == 403

    @pytest.mark.parametrize(
        "scopes, access",
        [
            (["*"], True),
            (["*", "location:Lon"], True),
            (["department:HR", "department:IT"], True),
            (["department:HR", "department:IT", "location:Lon"], True),
            (["department:HR"], False),
            (["department:HR", "location:Lon"], False),
        ],
    )
    def test_get_asset(
        self, db_session: Session, scopes: list[str], access: bool
    ) -> None:
        """Test getting a single asset based on user role and scope"""
        user = create_user(db_session)
        for scope in scopes:
            create_role(db_session, user_id=user.id, role="ReadAsset", scope=scope)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/assets/7", headers=headers)

        assert response.status_code == (200 if access else 403)

    def test_get_asset_doesnt_exist(self, db_session: Session) -> None:
        """Test getting a single asset based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/assets/999", headers=headers)

        assert response.status_code == 404

    def test_update_asset(self, db_session: Session) -> None:
        """Test updating an asset based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")

        token = auth.authenticate_user(user)
        asset_update_data: dict[str, Any] = {
            "name": "Updated Laptop",
            "description": "Updated",
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put("/api/assets/7", json=asset_update_data, headers=headers)

        assert response.status_code == 200

    def test_update_asset_forbidden(self, db_session: Session) -> None:
        """Test updating an asset based on user role and scope"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="CreateEditAsset", scope="location:Man"
        )

        token = auth.authenticate_user(user)
        asset_update_data: dict[str, Any] = {
            "name": "Updated Laptop",
            "description": "Updated",
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put("/api/assets/7", json=asset_update_data, headers=headers)

        assert response.status_code == 403

    def test_update_asset_doesnt_exist(self, db_session: Session) -> None:
        """Test updating an asset based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="CreateEditAsset", scope="*")

        token = auth.authenticate_user(user)
        asset_update_data: dict[str, Any] = {
            "name": "Updated Laptop",
            "description": "Updated",
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(
            "/api/assets/999", json=asset_update_data, headers=headers
        )

        assert response.status_code == 404

    def test_delete_asset(self, db_session: Session) -> None:
        """Test soft deleting an asset based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="RetireAsset", scope="*")

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete("/api/assets/7", headers=headers)

        assert response.status_code == 200
        assert initial_count == count_elements_in_db(db_session)

    def test_delete_asset_forbidden(self, db_session: Session) -> None:
        """Test soft deleting an asset based on user role and scope"""
        user = create_user(db_session)
        create_role(
            db_session, user_id=user.id, role="RetireAsset", scope="location:Man"
        )

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete("/api/assets/7", headers=headers)

        assert response.status_code == 403
        assert initial_count == count_elements_in_db(db_session)

    def test_delete_asset_doesnt_exist(self, db_session: Session) -> None:
        """Test soft deleting an asset based on user role and scope"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="RetireAsset", scope="*")

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete("/api/assets/999", headers=headers)

        assert response.status_code == 404
        assert initial_count == count_elements_in_db(db_session)

    def test_link_unlink_assets(self, db_session: Session) -> None:
        """Test linking and unlinking assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="ReadAsset", scope="*")
        create_role(db_session, user_id=user.id, role="LinkAsset", scope="*")

        asset1 = create_asset(db_session)
        asset2 = create_asset(db_session)

        initial_count = count_elements_in_db(db_session)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {"linked_id": asset2.id, "relation": "License"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assets/{asset1.id}/link", json=asset_data, headers=headers
        )

        assert response.status_code == 200
        assert (initial_count + 1) == count_elements_in_db(db_session)

        response = client.get(f"/api/assets/{asset1.id}", headers=headers)

        assert response.status_code == 200
        json = response.json()
        assert len(json["linked_assets"]) == 1
        assert json["linked_assets"][0]["asset_id"] == asset1.id
        assert json["linked_assets"][0]["linked_id"] == asset2.id

        response = client.get(f"/api/assets/{asset2.id}", headers=headers)

        assert response.status_code == 200
        json = response.json()
        assert len(json["linked_to"]) == 1
        assert json["linked_to"][0]["asset_id"] == asset1.id
        assert json["linked_to"][0]["linked_id"] == asset2.id

        response = client.delete(
            f"/api/assets/{asset1.id}/link/{asset2.id}", headers=headers
        )

        assert response.status_code == 200
        assert initial_count == count_elements_in_db(db_session)

    @pytest.mark.parametrize("asset1, asset2", [(1, 999), (999, 1), (999, 999)])
    def test_link_assets_invalid(
        self, db_session: Session, asset1: int, asset2: int
    ) -> None:
        """Test linking invalid assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="LinkAsset", scope="*")

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {"linked_id": asset2, "relation": "License"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            f"/api/assets/{asset1}/link", json=asset_data, headers=headers
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("asset1, asset2", [(1, 999), (999, 1), (999, 999), (1, 2)])
    def test_unlink_assets_invalid(
        self, db_session: Session, asset1: int, asset2: int
    ) -> None:
        """Test unlinking invalid assets"""
        user = create_user(db_session)
        create_role(db_session, user_id=user.id, role="LinkAsset", scope="*")

        token = auth.authenticate_user(user)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"/api/assets/{asset1}/link/{asset2}", headers=headers)

        assert response.status_code == 404

    def test_link_assets_valid_scope(self, db_session: Session) -> None:
        """Test linking assets with scopes"""
        user = create_user(db_session)
        for scope in ["department:HR", "location:Lon"]:
            create_role(db_session, user_id=user.id, role="LinkAsset", scope=scope)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {"linked_id": 5, "relation": "License"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/assets/6/link", json=asset_data, headers=headers)

        assert response.status_code == 200

    def test_link_assets_invalid_scope(self, db_session: Session) -> None:
        """Test linking invalid assets with scopes"""
        user = create_user(db_session)
        for scope in ["department:HR", "location:Man"]:
            create_role(db_session, user_id=user.id, role="LinkAsset", scope=scope)

        token = auth.authenticate_user(user)
        asset_data: dict[str, Any] = {"linked_id": 5, "relation": "License"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/assets/6/link", json=asset_data, headers=headers)

        assert response.status_code == 403
