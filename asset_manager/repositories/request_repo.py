# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the class to perform CRUD operations on Requests"""

from asset_manager.db.models.request import Request
from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo


class RequestRepository(AbstractCRUDRepo[Request]):
    """A class to perform CRUD operations on the repository of Requests in the database"""

    def get_requests_by_user(self, user_id: int) -> list[Request]:
        """Get all the requests made by a user"""
        return self.db.query(Request).filter(Request.user_id == user_id).all()
