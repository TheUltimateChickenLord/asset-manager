"""Defines Pydantic schemas for assets"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel

from asset_manager.schemas.labels import LabelSchema


class LinkedAssetSchema(BaseModel):
    """Pydantic Schema for LinkedAssets"""

    id: int
    asset_id: int
    linked_id: int
    relation: Literal["License", "Consumable", "Peripheral"]


class CreateLinkedAssetSchema(BaseModel):
    """Pydantic Schema for creating LinkedAssets"""

    linked_id: int
    relation: Literal["License", "Consumable", "Peripheral"]


class AssetSchema(BaseModel):
    """Pydantic Schema for Assets"""

    id: int
    asset_tag: str
    name: str
    description: str
    status: Literal["Available", "In Use", "Maintenance", "Reserved"]
    purchase_date: date
    purchase_cost: float
    created_at: datetime
    last_maintenance: Optional[datetime]
    maintenance_rate: int
    is_deleted: bool
    linked_assets: list[LinkedAssetSchema]
    linked_to: list[LinkedAssetSchema]
    labels: list[LabelSchema]


class RequestReturnSchema(BaseModel):
    """Pydantic Schema for requesting the return of Assets"""

    id: int


class CreateAssetSchema(BaseModel):
    """Pydantic Schema for creating Assets"""

    asset_tag: str
    name: str
    description: str
    purchase_date: date
    purchase_cost: float
    maintenance_rate: int
    labels: list[str]


class UpdateAssetSchema(BaseModel):
    """Pydantic Schema for updating Assets"""

    asset_tag: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    maintenance_rate: Optional[int] = None
