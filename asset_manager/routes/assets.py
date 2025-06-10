# pylint: disable=too-many-arguments, too-many-positional-arguments
"""Defines all the routes for assets"""

import json
from typing import Literal

from fastapi import APIRouter, HTTPException, status

from asset_manager.core.auth import CurrentActiveUser
from asset_manager.core.authz_utils import (
    get_assets_by_labels,
    get_labels_by_roles,
    has_role,
)
from asset_manager.core.logger import log_db_usage
from asset_manager.db.models.asset import Asset
from asset_manager.db.session import DependsDB
from asset_manager.repositories.asset_repo import AssetRepository
from asset_manager.repositories.label_mapping_repo import LabelMappingAssetRepository
from asset_manager.repositories.label_repo import LabelRepository
from asset_manager.repositories.linked_asset_repo import LinkedAssetRepository
from asset_manager.repositories.role_repo import RoleRepository
from asset_manager.schemas.asset import (
    AssetSchema,
    CreateAssetSchema,
    CreateLinkedAssetSchema,
    LinkedAssetSchema,
    UpdateAssetSchema,
)
from asset_manager.schemas.cast import cast_to_pydantic


router = APIRouter(tags=["Assets"])


def asset_exists(asset_id: int, repo: AssetRepository) -> Asset:
    """Returns whether an asset exists or not"""
    asset = repo.get_by_id(asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    return asset


@router.get("/")
def get_assets(db: DependsDB, current_user: CurrentActiveUser) -> list[AssetSchema]:
    """Gets a list of all the assets in the database that the current user is allowed to query"""
    repo = AssetRepository(db)
    role_repo = RoleRepository(db)

    if role_repo.has_scope_all(current_user.id, "ReadAsset"):
        log_db_usage("select", "assets", current_user.email, "Accessed all assets")
        return cast_to_pydantic(repo.get_all(), AssetSchema)

    roles = [role.scope for role in role_repo.get_roles(current_user.id, "ReadAsset")]
    if len(roles) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access assets"
        )

    log_db_usage("select", "assets", current_user.email, "Accessed all assets")

    return cast_to_pydantic(
        repo.get_all(subquery=get_assets_by_labels(get_labels_by_roles(db, roles))),
        AssetSchema,
    )


@router.post("/")
def create_asset(
    asset: CreateAssetSchema, db: DependsDB, current_user: CurrentActiveUser
) -> AssetSchema:
    """Create a new asset in the database"""
    if len(asset.labels) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset must have at least one label",
        )
    if not has_role(current_user, "CreateEditAsset", asset.labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create asset with label provided",
        )

    repo = AssetRepository(db)
    label_repo = LabelRepository(db)
    label_mapping_repo = LabelMappingAssetRepository(db)

    labels = [label_repo.get_by_name(label_name) for label_name in asset.labels]
    if any(label is None for label in labels):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One of your labels is not real",
        )

    data = asset.model_dump()
    del data["labels"]
    created_asset = repo.create(Asset(**data))
    log_db_usage(
        "insert",
        "assets",
        current_user.email,
        f"Created asset {created_asset.id} with info {json.dumps(data, default=str)}",
    )

    for label in labels:
        label_mapping_repo.create(
            {"item_id": created_asset.id, "label_id": label.id}  # type: ignore
        )
        log_db_usage(
            "insert",
            "label_mapping_assets",
            current_user.email,
            f"Mapped asset {created_asset.id} to label {label.id}",  # type: ignore
        )

    return cast_to_pydantic(created_asset, AssetSchema)


@router.get("/status/")
def get_assets_by_status(
    asset_status: Literal["Available", "In Use", "Maintenance", "Reserved"],
    db: DependsDB,
    current_user: CurrentActiveUser,
) -> list[AssetSchema]:
    """Gets a list of all the assets in the database by their status"""
    repo = AssetRepository(db)
    role_repo = RoleRepository(db)
    if role_repo.has_scope_all(current_user.id, "ReadAsset"):
        log_db_usage(
            "select",
            "assets",
            current_user.email,
            f"Accessed all assets with status {asset_status}",
        )
        return cast_to_pydantic(repo.get_by_status(asset_status), AssetSchema)

    roles = [role.scope for role in role_repo.get_roles(current_user.id, "ReadAsset")]
    if len(roles) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access assets"
        )

    log_db_usage(
        "select",
        "assets",
        current_user.email,
        f"Accessed all assets with status {asset_status}",
    )

    return cast_to_pydantic(
        repo.get_by_status(
            asset_status, subquery=get_assets_by_labels(get_labels_by_roles(db, roles))
        ),
        AssetSchema,
    )


@router.get("/{asset_id}/")
def get_asset(
    asset_id: int, db: DependsDB, current_user: CurrentActiveUser
) -> AssetSchema:
    """Gets an asset in the database by its ID"""
    repo = AssetRepository(db)
    asset = asset_exists(asset_id, repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "ReadAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create asset with label provided",
        )

    log_db_usage("select", "assets", current_user.email, f"Accessed asset {asset_id}")

    return cast_to_pydantic(asset, AssetSchema)


@router.put("/{asset_id}/")
def update_asset(
    asset_id: int,
    data: UpdateAssetSchema,
    db: DependsDB,
    current_user: CurrentActiveUser,
) -> AssetSchema:
    """Update the information about an asset in the database"""
    repo = AssetRepository(db)
    asset = asset_exists(asset_id, repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "CreateEditAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update asset",
        )

    log_db_usage(
        "update",
        "assets",
        current_user.email,
        f"Updated asset {asset_id} with info {json.dumps(data.model_dump(), default=str)}",
    )

    return cast_to_pydantic(
        repo.update(asset, {k: v for k, v in data.model_dump().items() if v}),
        AssetSchema,
    )


@router.delete("/{asset_id}/")
def delete_asset(
    asset_id: int,
    db: DependsDB,
    current_user: CurrentActiveUser,
) -> AssetSchema:
    """Soft delete an asset in the database"""
    repo = AssetRepository(db)
    asset = asset_exists(asset_id, repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "RetireAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot retire asset",
        )

    log_db_usage(
        "delete", "assets", current_user.email, f"Soft deleted asset {asset_id}"
    )

    return cast_to_pydantic(repo.delete(asset), AssetSchema)


@router.post("/{asset_id}/link/")
def link_assets(
    asset_id: int,
    config: CreateLinkedAssetSchema,
    db: DependsDB,
    current_user: CurrentActiveUser,
) -> LinkedAssetSchema:
    """Links one or more assets to an asset in the database"""
    asset_repo = AssetRepository(db)
    linked_repo = LinkedAssetRepository(db)

    asset1 = asset_exists(asset_id, asset_repo)
    asset2 = asset_exists(config.linked_id, asset_repo)

    labels = set(
        [label.name for label in asset1.labels]
        + [label.name for label in asset2.labels]
    )
    if not has_role(current_user, "LinkAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot link assets",
        )

    log_db_usage(
        "insert",
        "linked_assets",
        current_user.email,
        f"Linked assets {asset1.id} and {asset2.id} with relation {config.relation}",
    )

    return cast_to_pydantic(
        linked_repo.create(
            {"asset_id": asset1.id, "linked_id": asset2.id, "relation": config.relation}
        ),
        LinkedAssetSchema,
    )


@router.delete("/{asset_id}/link/{linked_id}/")
def unlink_assets(
    asset_id: int,
    linked_id: int,
    db: DependsDB,
    current_user: CurrentActiveUser,
) -> LinkedAssetSchema:
    """Deletes a link between assets in the database"""
    asset_repo = AssetRepository(db)
    linked_repo = LinkedAssetRepository(db)

    asset1 = asset_exists(asset_id, asset_repo)
    asset2 = asset_exists(linked_id, asset_repo)

    link = linked_repo.get_link(asset1.id, asset2.id)
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assets are not linked"
        )

    labels = set(
        [label.name for label in asset1.labels]
        + [label.name for label in asset2.labels]
    )
    if not has_role(current_user, "LinkAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot unlink assets",
        )

    log_db_usage(
        "delete",
        "linked_assets",
        current_user.email,
        f"Unlinked assets {asset1.id} and {asset2.id}",
    )

    return cast_to_pydantic(linked_repo.delete(link), LinkedAssetSchema)
