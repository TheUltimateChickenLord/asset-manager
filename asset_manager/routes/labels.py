# pylint: disable=too-many-arguments, too-many-positional-arguments
"""Defines all the routes for labels"""

from fastapi import APIRouter, HTTPException, status

from asset_manager.core.auth import CurrentActiveUser
from asset_manager.core.authz_utils import has_role
from asset_manager.core.logger import log_db_usage
from asset_manager.db.models.label import Label
from asset_manager.db.session import DependsDB
from asset_manager.repositories.asset_repo import AssetRepository
from asset_manager.repositories.label_mapping_repo import (
    LabelMappingAssetRepository,
    LabelMappingUserRepository,
)
from asset_manager.repositories.label_repo import LabelRepository
from asset_manager.repositories.user_repo import UserRepository
from asset_manager.routes.assets import asset_exists
from asset_manager.routes.user import user_exists
from asset_manager.schemas.labels import (
    CreateLabelMappingSchema,
    LabelMappingSchema,
    LabelSchema,
    CreateLabelSchema,
)
from asset_manager.schemas.cast import cast_to_pydantic


router = APIRouter(tags=["Labels"])


def label_exists(label_id: int, repo: LabelRepository) -> Label:
    """Returns whether an label exists or not"""
    label = repo.get_by_id(label_id)
    if label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )
    return label


@router.get("/")
def get_labels(db: DependsDB, current_user: CurrentActiveUser) -> list[LabelSchema]:
    """Gets all the labels in the database"""
    repo = LabelRepository(db)
    log_db_usage("select", "labels", current_user.email, "Accessed all labels")
    return cast_to_pydantic(repo.get_all(), LabelSchema)


@router.post("/")
def create_label(
    data: CreateLabelSchema, db: DependsDB, current_user: CurrentActiveUser
) -> LabelSchema:
    """Creates a new label"""
    repo = LabelRepository(db)

    # Must be able to create/edit any user or any asset to be able to create a new label
    # otherwise no one will ever be able to use it
    if not (
        has_role(current_user, "CreateEditUser", "*")
        or has_role(current_user, "CreateEditAsset", "*")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot request asset return",
        )

    label = repo.get_by_name(data.name)
    if label is None:
        log_db_usage(
            "insert",
            "labels",
            current_user.email,
            f"Created new label with name {data.name}",
        )
        return cast_to_pydantic(repo.create({"name": data.name}), LabelSchema)

    log_db_usage(
        "select",
        "labels",
        current_user.email,
        f"Tried to create label {label.id} but it already exited",
    )
    return cast_to_pydantic(label, LabelSchema)


@router.post("/assign/user/{user_id}/", tags=["Users"])
def assign_label_to_user(
    user_id: int,
    data: CreateLabelMappingSchema,
    db: DependsDB,
    current_user: CurrentActiveUser,
) -> LabelMappingSchema:
    """Assigns a label to a user"""
    repo = LabelMappingUserRepository(db)
    label_repo = LabelRepository(db)
    user_repo = UserRepository(db)

    user = user_exists(user_id, user_repo)

    label = label_exists(data.label_id, label_repo)

    labels = [label.name for label in user.labels] + [label.name]
    if not has_role(current_user, "CreateEditUser", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign label to user",
        )

    log_db_usage(
        "insert",
        "label_mapping_user",
        current_user.email,
        f"Assigned label {label.name} to user {user_id}",
    )

    return cast_to_pydantic(
        repo.create({"item_id": user_id, "label_id": data.label_id}), LabelMappingSchema
    )


@router.post("/assign/asset/{asset_id}/", tags=["Assets"])
def assign_label_to_asset(
    asset_id: int,
    data: CreateLabelMappingSchema,
    db: DependsDB,
    current_user: CurrentActiveUser,
) -> LabelMappingSchema:
    """Assigns a label to an asset"""
    repo = LabelMappingAssetRepository(db)
    label_repo = LabelRepository(db)
    asset_repo = AssetRepository(db)

    asset = asset_exists(asset_id, asset_repo)

    label = label_exists(data.label_id, label_repo)

    labels = [label.name for label in asset.labels] + [label.name]
    if not has_role(current_user, "CreateEditAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign label to asset",
        )

    log_db_usage(
        "insert",
        "label_mapping_asset",
        current_user.email,
        f"Assigned label {label.name} to asset {asset_id}",
    )

    return cast_to_pydantic(
        repo.create({"item_id": asset_id, "label_id": data.label_id}),
        LabelMappingSchema,
    )


@router.delete("/assign/user/{user_id}/", tags=["Users"])
def unassign_label_from_user(
    user_id: int, label_id: int, db: DependsDB, current_user: CurrentActiveUser
) -> LabelMappingSchema:
    """Deletes a label from a user"""
    repo = LabelMappingUserRepository(db)
    user_repo = UserRepository(db)

    mapping = repo.get_by_user_and_label(user_id, label_id)
    if mapping is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label mapping not found"
        )

    user = user_exists(user_id, user_repo)

    labels = [label.name for label in user.labels]
    if not has_role(current_user, "CreateEditUser", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot unassign label from user",
        )

    log_db_usage(
        "delete",
        "label_mapping_user",
        current_user.email,
        f"Unassigned label {label_id} from user {user_id}",
    )

    return cast_to_pydantic(repo.delete(mapping), LabelMappingSchema)


@router.delete("/assign/asset/{asset_id}/", tags=["Assets"])
def unassign_label_from_asset(
    asset_id: int, label_id: int, db: DependsDB, current_user: CurrentActiveUser
) -> LabelMappingSchema:
    """Deletes a label from an asset"""
    repo = LabelMappingAssetRepository(db)
    asset_repo = AssetRepository(db)

    mapping = repo.get_by_asset_and_label(asset_id, label_id)
    if mapping is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label mapping not found"
        )

    asset = asset_exists(asset_id, asset_repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "CreateEditAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot unassign label from asset",
        )

    log_db_usage(
        "delete",
        "label_mapping_asset",
        current_user.email,
        f"Unassigned label {label_id} from asset {asset_id}",
    )

    return cast_to_pydantic(repo.delete(mapping), LabelMappingSchema)


@router.get("/{label_id}/")
def get_label(
    label_id: int, db: DependsDB, current_user: CurrentActiveUser
) -> LabelSchema:
    """Get a label"""
    repo = LabelRepository(db)

    label = label_exists(label_id, repo)

    log_db_usage("select", "assets", current_user.email, f"Accessed label {label.name}")

    return cast_to_pydantic(label, LabelSchema)
