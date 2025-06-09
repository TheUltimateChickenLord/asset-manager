"""
Module defining all the security related components of the application,
including hashing, salting and JWTs
"""

import os
import hashlib
import re
import secrets
import string
from typing import Any
from datetime import datetime, timedelta, timezone

import jwt


SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise RuntimeError("No SECRET_KEY for JWT")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5"))

password_regex = re.compile(
    r"^(?=.{8,}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])"
)


def hash_password(password: str):
    """Securely hash a password and generate a ranom salt too"""
    salt = os.urandom(16).hex()
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100000
    ).hex()
    return pw_hash, salt


def verify_password(password: str, salt: str, hash_val: str):
    """Verify a password with ts hash"""
    return (
        hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        == hash_val
    )


def create_jwt(data: dict[str, Any]):
    """Create a JWT from data"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore
    return encoded_jwt


def decode_jwt(token: str):
    """Decrypt a JWT"""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore


def create_password() -> str:
    """Creates a random password"""
    character_list = string.ascii_letters + string.digits + string.punctuation
    while not verify_password_complexity(
        password := "".join(secrets.choice(character_list) for _ in range(10))
    ):
        pass
    return password


def verify_password_complexity(password: str) -> bool:
    """Verifies a password against the required criteria"""
    return password_regex.match(password) is not None
