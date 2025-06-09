# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the abstract class for CRUD operations"""

from abc import ABC
from typing import Any, Generic, Optional, TypeVar, Union, get_args

from sqlalchemy import ColumnExpressionArgument
from sqlalchemy.orm import Session

from asset_manager.db.base import Base


T = TypeVar("T", bound=Base)


class AbstractCRUDRepo(ABC, Generic[T]):
    """An abstract class for repositories that contains all the CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    @property
    def model(self) -> type[T]:
        """A variable containing the generic class provided by the child class"""
        return get_args(getattr(self, "__orig_bases__")[0])[0]

    def get_all(
        self,
        include_deleted: bool = False,
        subquery: Optional[ColumnExpressionArgument[bool]] = None,
    ) -> list[T]:
        """Get all items in repo"""
        filters: list[ColumnExpressionArgument[bool]] = []

        if subquery is not None:
            filters.append(subquery)
        if not include_deleted and hasattr(self.model, "is_deleted"):
            filters.append(getattr(self.model, "is_deleted") == False)

        if len(filters) > 0:
            return self.db.query(self.model).filter(*filters).all()
        return self.db.query(self.model).all()

    def get_by_id(self, item_id: int, include_deleted: bool = True) -> Optional[T]:
        """Get an item in the repo by its primary key (id)"""
        item: Optional[T] = self.db.get(self.model, item_id)
        if (
            not include_deleted
            and item is not None
            and hasattr(self.model, "is_deleted")
        ):
            if getattr(self.model, "is_deleted"):
                return None
        return item

    def create(self, item: Union[T, dict[str, Any]]) -> T:
        """Create a new item in the repo"""
        if isinstance(item, dict):
            item = self.model(**item)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item: T, data: dict[str, Any]) -> T:
        """Update an item in the repo"""
        for key, value in data.items():
            if value is not None:
                setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: T) -> T:
        """Soft delete an item in the repo if possible otherwise fully delete it"""
        if not hasattr(self.model, "is_deleted"):
            self.db.delete(item)
        else:
            setattr(item, "is_deleted", True)
        self.db.commit()
        if hasattr(self.model, "is_deleted"):
            self.db.refresh(item)
        return item
