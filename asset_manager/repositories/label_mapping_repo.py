# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the class to perform CRUD operations on LabelMappings"""

from typing import Optional

from asset_manager.db.models.label_mapping import LabelMappingAsset, LabelMappingUser
from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo


class LabelMappingAssetRepository(AbstractCRUDRepo[LabelMappingAsset]):
    """A class to perform CRUD operations on the repository of LabelMappingAssets in the database"""

    def get_by_asset_and_label(
        self, asset_id: int, label_id: int
    ) -> Optional[LabelMappingAsset]:
        """Get a label mapping by the asset and label that it links"""
        return (
            self.db.query(LabelMappingAsset)
            .filter(
                LabelMappingAsset.item_id == asset_id,
                LabelMappingAsset.label_id == label_id,
            )
            .first()
        )


class LabelMappingUserRepository(AbstractCRUDRepo[LabelMappingUser]):
    """A class to perform CRUD operations on the repository of LabelMappingUsers in the database"""

    def get_by_user_and_label(
        self, user_id: int, label_id: int
    ) -> Optional[LabelMappingUser]:
        """Get a label mapping by the user and label that it links"""
        return (
            self.db.query(LabelMappingUser)
            .filter(
                LabelMappingUser.item_id == user_id,
                LabelMappingUser.label_id == label_id,
            )
            .first()
        )
