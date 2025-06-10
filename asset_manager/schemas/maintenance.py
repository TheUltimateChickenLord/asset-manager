"""Defines Pydantic schemas for maintenance"""

from pydantic import BaseModel


class MaintainAssetSchema(BaseModel):
    """Pydantic Schema for checking in and out Assets for maintenance"""

    asset_id: int
