"""Module defining all the auth related components of the application"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from asset_manager.core.security import decode_jwt, verify_password
from asset_manager.db.models.user import User
from asset_manager.db.session import get_db
from asset_manager.repositories.user_repo import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def authenticate_user(repo: UserRepository, email: str, password: str):
    """Authenticate a user against the database"""
    user = repo.get_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.password_salt, user.password_hash):
        return None
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
):
    """FastAPI dependency to get the current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt(token)
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError as exc:
        raise credentials_exception from exc
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(
    current_user: CurrentUser,
):
    """
    FastAPI dependency to get the current user and check if they are active or need to reset
    their password
    """
    if current_user.is_disabled or current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )
    if current_user.reset_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You need to reset your password first",
        )
    return current_user


async def get_current_active_user_password_reset_routes(
    current_user: CurrentUser,
):
    """FastAPI dependency to get the current user and check if they are active"""
    if current_user.is_disabled or current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )
    return current_user


CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentActiveUserPasswordResetRoutes = Annotated[
    User, Depends(get_current_active_user_password_reset_routes)
]
