from typing import Any
import pytest

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from asset_manager import main
from asset_manager.core import security
from asset_manager.db import session
from asset_manager.db.base import Base
from tests.data import seed
from tests.data.model_creators import create_user
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


class TestAuth:
    """Test class for managing auth routes in the FastAPI application"""

    def test_valid_login(self, db_session: Session):
        """Test a login with valid credentials"""
        password = "Password123!"

        pw_hash, salt = security.hash_password(password)
        user = create_user(db_session, password_hash=pw_hash, password_salt=salt)

        asset_data: dict[str, Any] = {
            "username": user.email,
            "password": password,
        }
        response = client.post(f"/token", data=asset_data)

        assert response.status_code == 200

    def test_invalid_login(self, db_session: Session):
        """Test a login with invalid credentials"""
        password = "Password123!"

        pw_hash, salt = security.hash_password(password)
        user = create_user(db_session, password_hash=pw_hash, password_salt=salt)

        asset_data: dict[str, Any] = {
            "username": user.email,
            "password": password[:-1],
        }
        response = client.post(f"/token", data=asset_data)

        assert response.status_code == 401
