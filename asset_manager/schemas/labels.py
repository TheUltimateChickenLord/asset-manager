"""Defines Pydantic schemas for labels"""

from pydantic import BaseModel


class LabelSchema(BaseModel):
    """Pydantic Schema for Labels"""

    id: int
    name: str


class CreateLabelSchema(BaseModel):
    """Pydantic Schema for creating Labels"""

    name: str


class LabelMappingSchema(BaseModel):
    """Pydantic Schema for LabelMappings"""

    item_id: int
    label_id: int


class CreateLabelMappingSchema(BaseModel):
    """Pydantic Schema for creating LabelMappings"""

    label_id: int
