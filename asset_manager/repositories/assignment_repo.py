# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the class to perform CRUD operations on AssetAssignments"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import or_

from asset_manager.db.models.asset import Asset
from asset_manager.db.models.assignment import AssetAssignment
from asset_manager.db.models.request import Request
from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo


class AssetAssignmentRepository(AbstractCRUDRepo[AssetAssignment]):
    """A class to perform CRUD operations on the repository of AssetAssignments in the database"""

    def check_out_asset(
        self, asset: Asset, user_id: int, assigned_by_id: int, due_in_days: int
    ) -> AssetAssignment:
        """Check out an asset by creating an assignment"""
        assignment = AssetAssignment(
            asset_id=asset.id,
            user_id=user_id,
            assigned_by_id=assigned_by_id,
            due_date=date.today() + timedelta(days=due_in_days),
        )
        return self.create(assignment)

    def check_out_asset_request(
        self, request: Request, assigned_by_id: int, due_in_days: int
    ) -> AssetAssignment:
        """Check out an asset by creating an assignment"""
        assignment = AssetAssignment(
            asset_id=request.asset.id,
            user_id=request.user_id,
            assigned_by_id=assigned_by_id,
            due_date=date.today() + timedelta(days=due_in_days),
            request_id=request.id,
        )
        return self.create(assignment)

    def get_asset_assignment(self, asset_id: int) -> Optional[AssetAssignment]:
        """Get the current assignment for an asset"""
        return (
            self.db.query(AssetAssignment)
            .filter(
                AssetAssignment.returned_at == None,
                AssetAssignment.asset_id == asset_id,
            )
            .first()
        )

    def get_by_user(self, user_id: int) -> list[AssetAssignment]:
        """Get all the assignments where a user is the assigner or assignee"""
        return (
            self.db.query(AssetAssignment)
            .filter(
                or_(
                    AssetAssignment.assigned_by_id == user_id,
                    AssetAssignment.user_id == user_id,
                )
            )
            .all()
        )

    def get_overdue(self, user_id: int, due_in_days: int) -> list[AssetAssignment]:
        """Get all the assignments that are due in the next `due_in_days` days"""
        return (
            self.db.query(AssetAssignment)
            .filter(
                or_(
                    AssetAssignment.assigned_by_id == user_id,
                    AssetAssignment.user_id == user_id,
                ),
                AssetAssignment.due_date
                <= (date.today() + timedelta(days=due_in_days)),
                AssetAssignment.returned_at == None,
            )
            .all()
        )
