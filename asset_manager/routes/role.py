# pylint: disable=too-many-arguments, too-many-positional-arguments
"""Defines all the routes for roles"""

from fastapi import APIRouter, HTTPException, status

from asset_manager.core.auth import CurrentActiveUser
from asset_manager.core.authz_utils import has_role
from asset_manager.core.logger import log_db_usage
from asset_manager.db.session import DependsDB
from asset_manager.repositories.label_repo import LabelRepository
from asset_manager.repositories.role_repo import RoleRepository, roles
from asset_manager.repositories.user_repo import UserRepository
from asset_manager.routes.user import user_exists
from asset_manager.schemas.cast import cast_to_pydantic
from asset_manager.schemas.role import RoleSchema


router = APIRouter(tags=["Roles"])


@router.get("/")
def get_all_roles() -> list[str]:
    """Gets all the available roles"""
    return roles


@router.get("/user/{user_id}/", tags=["Users"])
def get_roles_for_user(
    user_id: int, current_user: CurrentActiveUser, db: DependsDB
) -> list[RoleSchema]:
    """Gets all the roles for a user based on their ID"""
    repo = RoleRepository(db)
    user_repo = UserRepository(db)

    user = user_exists(user_id, user_repo)

    labels = [label.name for label in user.labels]
    if not (has_role(current_user, "ReadUser", labels) or user_id == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot read user roles",
        )

    log_db_usage(
        "select", "roles", current_user.email, f"Accessed user {user_id} roles"
    )

    return cast_to_pydantic(repo.get_roles_by_user_id(user_id), RoleSchema)


@router.post("/user/{user_id}/", tags=["Users"])
def assign_role(
    user_id: int, role: RoleSchema, current_user: CurrentActiveUser, db: DependsDB
) -> RoleSchema:
    """Creates a new role for a user"""
    repo = RoleRepository(db)
    label_repo = LabelRepository(db)
    user_repo = UserRepository(db)

    user = user_exists(user_id, user_repo)

    if role.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    labels = [label.name for label in user.labels] + [role.scope]
    if role.scope != "*":
        label = label_repo.get_by_name(role.scope)
        if label is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role scope is not a label",
            )

    if not (
        has_role(current_user, "CreateEditUser", labels)
        and has_role(current_user, role.role, labels)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign user role",
        )

    log_db_usage(
        "insert",
        "roles",
        current_user.email,
        f"Assigned role {role.role} with scope {role.scope} to user {user_id}",
    )

    return cast_to_pydantic(
        repo.create({"user_id": user_id, "scope": role.scope, "role": role.role}),
        RoleSchema,
    )


@router.delete("/user/{user_id}/", tags=["Users"])
def delete_role(
    user_id: int, role: str, scope: str, current_user: CurrentActiveUser, db: DependsDB
) -> RoleSchema:
    """Removes a role from a user"""
    repo = RoleRepository(db)
    user_repo = UserRepository(db)

    user = user_exists(user_id, user_repo)

    labels = [label.name for label in user.labels] + [scope]
    if not (
        has_role(current_user, "CreateEditUser", labels)
        and has_role(current_user, role, labels)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot unassign user role",
        )

    role_obj = repo.get_role(user_id, role, scope)
    if role_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    log_db_usage(
        "delete",
        "roles",
        current_user.email,
        f"Unassigned role {role} with scope {scope} to user {user_id}",
    )

    return cast_to_pydantic(repo.delete(role_obj), RoleSchema)
