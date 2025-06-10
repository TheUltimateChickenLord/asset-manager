# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the class to perform CRUD operations on Assets"""

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from sqlalchemy import ColumnExpressionArgument

from asset_manager.db.models.asset import Asset
from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo


class AssetRepository(AbstractCRUDRepo[Asset]):
    """A class to perform CRUD operations on the repository of Assets in the database"""

    def get_by_status(
        self,
        status: Literal["Available", "In Use", "Maintenance", "Reserved"],
        include_deleted: bool = False,
        subquery: Optional[ColumnExpressionArgument[bool]] = None,
    ) -> list[Asset]:
        """Get assets by their status"""
        filters: list[ColumnExpressionArgument[bool]] = [Asset.status == status]

        if subquery is not None:
            filters.append(subquery)
        if not include_deleted:
            filters.append(Asset.is_deleted == False)

        return self.db.query(Asset).filter(*filters).all()

    def get_due_for_maintenance(
        self, subquery: Optional[ColumnExpressionArgument[bool]] = None
    ) -> list[Asset]:
        """Get assets that are due for maintenance"""
        assets = self.get_all(subquery=subquery)

        return [
            asset
            for asset in assets
            if asset.last_maintenance.replace(tzinfo=timezone.utc)
            + timedelta(days=asset.maintenance_rate)
            < datetime.now(timezone.utc)
        ]
