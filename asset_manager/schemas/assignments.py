"""Defines Pydantic schemas for asset assignments"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, PositiveInt

from asset_manager.schemas.asset import AssetSchema
from asset_manager.schemas.user import SmallUserSchema


class AssetAssignmentSchema(BaseModel):
    """Pydantic Schema for AssetAssignments"""

    id: int
    asset_id: int
    user_id: int
    assigned_by_id: int
    assigned_at: datetime
    due_date: date
    returned_at: Optional[datetime]
    request_id: Optional[int]
    asset: AssetSchema
    user: SmallUserSchema
    assigned_by: SmallUserSchema


class CheckInAssetSchema(BaseModel):
    """Pydantic Schema for checking in Assets"""

    asset_id: int


class CheckOutAssetSchema(BaseModel):
    """Pydantic Schema for checking out Assets"""

    asset_id: int
    user_id: int
    due_in_days: PositiveInt


class CheckOutAssetRequestSchema(BaseModel):
    """Pydantic Schema for checking out Assets by Request"""

    due_in_days: PositiveInt


class RequestReturnSchema(BaseModel):
    """Pydantic Schema for requesting the return of Assets"""

    asset_assignment_id: int
    due_in_days: int = Field(0, ge=0)
