# pylint: disable=too-many-arguments, too-many-positional-arguments
"""Defines all the routes for auth"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from asset_manager.core.auth import authenticate_user
from asset_manager.core.logger import log_db_usage
from asset_manager.core.security import create_jwt
from asset_manager.db.session import DependsDB
from asset_manager.repositories.user_repo import UserRepository
from asset_manager.schemas.auth import TokenSchema


router = APIRouter(tags=["Auth"])


@router.post("/token/")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DependsDB
) -> TokenSchema:
    """Returns a new JWT for the logged in user"""
    repo = UserRepository(db)
    user = authenticate_user(repo, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_jwt(data={"sub": user.email})

    log_db_usage("select", "users", user.email, "User generated a new token")

    return TokenSchema(access_token=access_token, token_type="bearer")
