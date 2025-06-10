# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the class to perform CRUD operations on Roles"""

from typing import Optional

from asset_manager.db.models.role import Role
from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo


roles = [
    "CreateEditUser",
    "ReadUser",
    "DeleteUser",
    "DisableUser",
    "ResetPasswordUser",
    "CreateEditAsset",
    "CheckInOutAsset",
    "ReadAsset",
    "RetireAsset",
    "LinkAsset",
    "RequestAsset",
]


class RoleRepository(AbstractCRUDRepo[Role]):
    """A class to perform CRUD operations on the repository of Roles in the database"""

    def get_roles_by_user_id(self, user_id: int) -> list[Role]:
        """Get all the roles that a user has"""
        return self.db.query(Role).filter(Role.user_id == user_id).all()

    def get_role(self, user_id: int, role: str, scope: str) -> Optional[Role]:
        """Get a role object from the db from its values"""
        return (
            self.db.query(Role)
            .filter(Role.user_id == user_id, Role.scope == scope, Role.role == role)
            .first()
        )

    def has_scope_all(self, user_id: int, role: str) -> bool:
        """Checks whether the user has the role with scope all (*)"""
        return self.get_role(user_id, role, "*") is not None

    def get_roles(self, user_id: int, role: str) -> list[Role]:
        """Gets the roles for a user"""
        return (
            self.db.query(Role).filter(Role.user_id == user_id, Role.role == role).all()
        )
