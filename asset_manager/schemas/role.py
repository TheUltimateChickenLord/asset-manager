"""Defines Pydantic schemas for roles"""

from pydantic import BaseModel


class RoleSchema(BaseModel):
    """Pydantic Schema for Roles"""

    role: str
    scope: str


class AllRolesSchema(BaseModel):
    """Pydantic Schema for Roles"""

    roles: list[str]
    scopes: list[str]
