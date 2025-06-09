import os
from importlib import reload

import pytest
import jwt

from asset_manager.core import security
from tests.data.reload import reload_all_modules


class TestSecurity:
    @pytest.fixture(autouse=True)
    def set_env_vars(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("SECRET_KEY", "testsecret")
        monkeypatch.setenv("ALGORITHM", "HS256")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1")
        monkeypatch.setenv("LOG_DIR", "tests/logs")
        reload_all_modules()

    @pytest.mark.parametrize(
        "password", ["Password123!", "Adm1N!12", "jhgasd Aadfgi12!", "`ghjA8367+=="]
    )
    def test_valid_passwords(self, password: str):
        assert security.verify_password_complexity(password)

    @pytest.mark.parametrize(
        "password", ["password123!", "PASSWORD123!", "Password!", "Password123", "aA!0"]
    )
    def test_invalid_passwords(self, password: str):
        assert not security.verify_password_complexity(password)

    def test_create_password(self):
        for _ in range(1000):
            assert security.verify_password_complexity(security.create_password())

    def test_hash_password_returns_hash_and_salt(self):
        password = "testpassword"
        pw_hash, salt = security.hash_password(password)
        assert isinstance(pw_hash, str)
        assert isinstance(salt, str)
        assert len(salt) > 0

    def test_verify_password_success(self):
        password = "secure123"
        pw_hash, salt = security.hash_password(password)
        assert security.verify_password(password, salt, pw_hash)

    def test_verify_password_failure_wrong_password(self):
        pw_hash, salt = security.hash_password("correct_password")
        assert not security.verify_password("wrong_password", salt, pw_hash)

    def test_verify_password_failure_wrong_salt(self):
        pw_hash, _ = security.hash_password("secure123")
        wrong_salt = os.urandom(16).hex()
        assert not security.verify_password("secure123", wrong_salt, pw_hash)

    def test_decode_jwt_valid(self):
        data = {"username": "example_name"}
        token = security.create_jwt(data)
        decoded = security.decode_jwt(token)
        assert decoded["username"] == "example_name"

    def test_decode_jwt_invalid_token(self):
        with pytest.raises(jwt.exceptions.InvalidTokenError):
            security.decode_jwt("this.is.an.invalid.token")

    def test_decode_jwt_expired(self, monkeypatch: pytest.MonkeyPatch):
        # Patch expiry to be in the past
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "-1")

        reload(security)

        token = security.create_jwt({"test": "expired"})
        with pytest.raises(jwt.ExpiredSignatureError):
            security.decode_jwt(token)
