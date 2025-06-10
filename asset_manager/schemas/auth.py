"""Defines Pydantic schemas for auth"""

from pydantic import BaseModel


class TokenSchema(BaseModel):
    """Pydantic Schema for JWTs"""

    access_token: str
    token_type: str
