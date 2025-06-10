"""Defines Pydantic schemas for users"""

from datetime import datetime

from pydantic import BaseModel

from asset_manager.schemas.labels import LabelSchema
from asset_manager.schemas.role import RoleSchema


class SmallUserSchema(BaseModel):
    """Pydantic Schema for Users returned in other responses"""

    id: int
    name: str
    email: str


class CreateUserSchema(BaseModel):
    """Pydantic Schema for creating new Users"""

    name: str
    email: str
    password: str
    labels: list[str]


class ResetPasswordSchema(BaseModel):
    """Pydantic Schema for resetting Users passwords"""

    password: str


class UserSchema(BaseModel):
    """Pydantic Schema for Users"""

    id: int
    name: str
    email: str
    is_disabled: bool
    is_deleted: bool
    created_at: datetime
    reset_password: bool
    labels: list[LabelSchema]
    roles: list[RoleSchema]
