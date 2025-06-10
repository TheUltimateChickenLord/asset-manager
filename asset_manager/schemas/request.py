"""Defines Pydantic schemas for requests"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from asset_manager.schemas.labels import LabelSchema
from asset_manager.schemas.user import SmallUserSchema


class AssignmentRequestSchema(BaseModel):
    """Pydantic Schema for AssetAssignments in Requests"""

    id: int


class AssetRequestSchema(BaseModel):
    """Pydantic Schema for Assets returned in requests"""

    id: int
    asset_tag: str
    name: str
    description: str
    labels: list[LabelSchema]


class RequestSchema(BaseModel):
    """Pydantic Schema for Requests"""

    id: int
    user_id: int
    asset_id: int
    status: Literal["Pending", "Approved", "Rejected", "Fulfilled"]
    justification: str
    requested_at: datetime
    approved_by: Optional[int]
    asset: AssetRequestSchema
    user: SmallUserSchema
    approver: Optional[SmallUserSchema]
    assignment: Optional[AssignmentRequestSchema]


class CreateRequestSchema(BaseModel):
    """Pydantic Schema for creating Requests"""

    asset_id: int
    justification: str


class RequestUpdateSchema(BaseModel):
    """Pydantic Schema for updating Requests"""

    id: int
