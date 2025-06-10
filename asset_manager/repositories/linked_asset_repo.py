# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the class to perform CRUD operations on LinkedAssets"""

from typing import Optional

from asset_manager.db.models.linked_asset import LinkedAsset
from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo


class LinkedAssetRepository(AbstractCRUDRepo[LinkedAsset]):
    """A class to perform CRUD operations on the repository of LinkedAssets in the database"""

    def get_linked_assets(self, asset_id: int) -> list[LinkedAsset]:
        """Get all the linked assets for an asset"""
        return self.db.query(LinkedAsset).filter(LinkedAsset.asset_id == asset_id).all()

    def get_link(self, asset_id: int, linked_id: int) -> Optional[LinkedAsset]:
        """Get a link object by the assets and their link"""
        return (
            self.db.query(LinkedAsset)
            .filter(
                LinkedAsset.asset_id == asset_id, LinkedAsset.linked_id == linked_id
            )
            .first()
        )
