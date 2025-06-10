# pylint: disable=too-many-arguments, too-many-positional-arguments
"""Defines all the routes for users"""

from fastapi import APIRouter, HTTPException, status

from asset_manager.core.auth import (
    CurrentActiveUser,
    CurrentActiveUserPasswordResetRoutes,
)
from asset_manager.core.authz_utils import (
    get_labels_by_roles,
    get_users_by_labels,
    has_role,
)
from asset_manager.core.logger import log_db_usage
from asset_manager.core.security import create_password, verify_password_complexity
from asset_manager.db.models.user import User
from asset_manager.db.session import DependsDB
from asset_manager.repositories.label_mapping_repo import LabelMappingUserRepository
from asset_manager.repositories.label_repo import LabelRepository
from asset_manager.repositories.role_repo import RoleRepository
from asset_manager.repositories.user_repo import UserRepository
from asset_manager.schemas.cast import cast_to_pydantic
from asset_manager.schemas.user import (
    CreateUserSchema,
    ResetPasswordSchema,
    UserSchema,
)


router = APIRouter(tags=["Users"])


def user_exists(user_id: int, repo: UserRepository) -> User:
    """Returns whether an user exists or not"""
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get("/")
def get_users(db: DependsDB, current_user: CurrentActiveUser) -> list[UserSchema]:
    """Gets a list of all the users in the database that the current user is allowed to query"""
    repo = UserRepository(db)
    role_repo = RoleRepository(db)

    if role_repo.has_scope_all(current_user.id, "ReadUser"):
        log_db_usage("select", "users", current_user.email, "Accessed all users")
        return cast_to_pydantic(repo.get_all(), UserSchema)

    roles = [role.scope for role in role_repo.get_roles(current_user.id, "ReadUser")]
    if len(roles) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access users"
        )

    log_db_usage("select", "users", current_user.email, "Accessed all users")

    return cast_to_pydantic(
        repo.get_all(subquery=get_users_by_labels(get_labels_by_roles(db, roles))),
        UserSchema,
    )


@router.get("/me/")
def get_myself(current_user: CurrentActiveUserPasswordResetRoutes) -> UserSchema:
    """Gets the information about the user who is currently logged in"""
    log_db_usage("select", "users", current_user.email, "Accessed themselves")
    return cast_to_pydantic(current_user, UserSchema)


@router.get("/{user_id}/")
def get_user(
    user_id: int, db: DependsDB, current_user: CurrentActiveUser
) -> UserSchema:
    """Gets the information about a user based on their ID"""
    repo = UserRepository(db)

    user = user_exists(user_id, repo)

    labels = [label.name for label in user.labels]
    if not (has_role(current_user, "ReadUser", labels) or user_id == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot read user",
        )

    log_db_usage("select", "users", current_user.email, f"Accessed user {user_id}")

    return cast_to_pydantic(user, UserSchema)


@router.post("/")
def create_user(
    data: CreateUserSchema, db: DependsDB, current_user: CurrentActiveUser
) -> UserSchema:
    """Creates a new user in the database"""
    if len(data.labels) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have at least one label",
        )
    if not has_role(current_user, "CreateEditUser", data.labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create user with label provided",
        )

    repo = UserRepository(db)
    label_repo = LabelRepository(db)
    label_mapping_repo = LabelMappingUserRepository(db)

    labels = [label_repo.get_by_name(label_name) for label_name in data.labels]
    if any(label is None for label in labels):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One of your labels is not real",
        )

    if repo.get_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )
    if repo.get_by_name(data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    if not verify_password_complexity(data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password doesn't meet complexity requirements",
        )

    user = repo.register_user(data.name, data.email, data.password)
    log_db_usage(
        "insert",
        "users",
        current_user.email,
        f'Created user {user.id} with info {{"name": "{data.name}", "email": "{data.email}"}}',
    )

    for label in labels:
        label_mapping_repo.create(
            {"item_id": user.id, "label_id": label.id}  # type: ignore
        )
        log_db_usage(
            "insert",
            "label_mapping_users",
            current_user.email,
            f"Mapped user {user.id} to label {label.id}",  # type: ignore
        )

    return cast_to_pydantic(
        user,
        UserSchema,
    )


@router.put("/reset-password/")
def reset_password_self(
    data: ResetPasswordSchema,
    db: DependsDB,
    current_user: CurrentActiveUserPasswordResetRoutes,
) -> str:
    """Resets a user's password in the database"""
    repo = UserRepository(db)

    repo.reset_password(current_user, data.password)

    log_db_usage("update", "users", current_user.email, "Reset password for themselves")

    return data.password


@router.put("/{user_id}/")
def enable_user(
    user_id: int, db: DependsDB, current_user: CurrentActiveUser
) -> UserSchema:
    """Enables a user account in the database"""
    repo = UserRepository(db)

    user = user_exists(user_id, repo)

    labels = [label.name for label in user.labels]

    if not has_role(current_user, "DisableUser", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot enable user",
        )

    log_db_usage("update", "users", current_user.email, f"Enabled user {user.id}")

    return cast_to_pydantic(repo.enable_user(user), UserSchema)


@router.delete("/{user_id}/")
def delete_user(
    user_id: int, db: DependsDB, current_user: CurrentActiveUser, temp: bool = False
) -> UserSchema:
    """Soft deletes a user in the database"""
    repo = UserRepository(db)

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete yourself"
        )

    user = user_exists(user_id, repo)

    labels = [label.name for label in user.labels]

    if temp:
        if not has_role(current_user, "DisableUser", labels):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot disable user",
            )

        log_db_usage("update", "users", current_user.email, f"Disabled user {user.id}")

        return cast_to_pydantic(repo.disable_user(user), UserSchema)

    if not has_role(current_user, "DeleteUser", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete user",
        )

    log_db_usage("delete", "users", current_user.email, f"Soft deleted user {user.id}")

    return cast_to_pydantic(repo.delete(user), UserSchema)


@router.put("/{user_id}/reset-password/")
def reset_password(user_id: int, db: DependsDB, current_user: CurrentActiveUser) -> str:
    """Resets a user's password in the database"""
    repo = UserRepository(db)

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /api/users/reset-password to reset your own password",
        )

    user = user_exists(user_id, repo)

    labels = [label.name for label in user.labels]
    if not has_role(current_user, "ResetPasswordUser", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot reset user password",
        )

    password = create_password()
    repo.reset_password(user, password, reset_required=True)

    log_db_usage("update", "users", current_user.email, f"Reset password for {user.id}")

    return password
