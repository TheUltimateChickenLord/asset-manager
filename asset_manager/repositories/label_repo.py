# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the class to perform CRUD operations on Labels"""

from typing import Optional

from asset_manager.db.models.label import Label
from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo


class LabelRepository(AbstractCRUDRepo[Label]):
    """A class to perform CRUD operations on the repository of Labels in the database"""

    def has_relationships(self, label: Label) -> bool:
        """Check if a label is linked to any other items"""
        return len(label.assets) != 0 or len(label.users) != 0

    def get_by_user(self, user_id: int) -> list[Label]:
        """Get all labels linked to a user"""
        return self.db.query(Label).filter(Label.users.any(id=user_id)).all()

    def get_by_name(self, name: str) -> Optional[Label]:
        """Get a label by its name"""
        return self.db.query(Label).filter(Label.name == name).first()
