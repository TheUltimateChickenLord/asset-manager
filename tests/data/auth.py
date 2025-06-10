"""Module containing auth utility functions to help with testing"""

from asset_manager.core.security import create_jwt
from asset_manager.db.models.user import User


def authenticate_user(user: User) -> str:
    """Authenticate a user and retrieve an access token"""
    return create_jwt(data={"sub": user.email})
