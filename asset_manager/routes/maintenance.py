# pylint: disable=too-many-arguments, too-many-positional-arguments, duplicate-code
"""Defines all the routes for labels"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from asset_manager.core.auth import CurrentActiveUser
from asset_manager.core.authz_utils import (
    get_assets_by_labels,
    get_labels_by_roles,
    has_role,
)
from asset_manager.core.logger import log_db_usage
from asset_manager.db.session import DependsDB
from asset_manager.repositories.asset_repo import AssetRepository
from asset_manager.repositories.role_repo import RoleRepository
from asset_manager.routes.assets import asset_exists
from asset_manager.schemas.asset import AssetSchema
from asset_manager.schemas.cast import cast_to_pydantic
from asset_manager.schemas.maintenance import MaintainAssetSchema


router = APIRouter(tags=["Maintenance"])


@router.post("/check-out/", tags=["Assets"])
def check_out_asset_for_maintenance(
    data: MaintainAssetSchema, current_user: CurrentActiveUser, db: DependsDB
) -> AssetSchema:
    """Check out an item for maintenance in the database"""
    asset_repo = AssetRepository(db)

    asset = asset_exists(data.asset_id, asset_repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot check out asset for maintenance",
        )

    if asset.status != "Available":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Asset status is not available"
        )

    asset = asset_repo.update(asset, {"status": "Maintenance"})
    log_db_usage(
        "update",
        "assets",
        current_user.email,
        f"Updated asset {asset.id} status to 'Maintenance'",
    )

    return cast_to_pydantic(
        asset,
        AssetSchema,
    )


@router.post("/check-in/", tags=["Assets"])
def check_in_asset_from_maintenance(
    data: MaintainAssetSchema, current_user: CurrentActiveUser, db: DependsDB
) -> AssetSchema:
    """Check in an item from maintenance"""
    asset_repo = AssetRepository(db)

    asset = asset_exists(data.asset_id, asset_repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot check in asset from maintenance",
        )

    if asset.status != "Maintenance":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset status is not Maintenance",
        )

    asset = asset_repo.update(
        asset, {"status": "Available", "last_maintenance": datetime.now(timezone.utc)}
    )
    log_db_usage(
        "update",
        "assets",
        current_user.email,
        f"Updated asset {asset.id} status to 'Available' and last_maintenance to current time",
    )

    return cast_to_pydantic(
        asset,
        AssetSchema,
    )


@router.get("/due/", tags=["Assets"])
def assets_due_for_maintenance(
    current_user: CurrentActiveUser, db: DependsDB
) -> list[AssetSchema]:
    """Get all assets that are due for maintenance"""
    repo = AssetRepository(db)
    role_repo = RoleRepository(db)

    if role_repo.has_scope_all(current_user.id, "ReadAsset"):
        log_db_usage(
            "select",
            "assets",
            current_user.email,
            "Accessed all assets due for maintenance",
        )
        return cast_to_pydantic(repo.get_due_for_maintenance(), AssetSchema)

    roles = [role.scope for role in role_repo.get_roles(current_user.id, "ReadAsset")]
    if len(roles) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access assets due for maintenance",
        )

    log_db_usage(
        "select",
        "assets",
        current_user.email,
        "Accessed all assets due for maintenance",
    )

    return cast_to_pydantic(
        repo.get_due_for_maintenance(
            subquery=get_assets_by_labels(get_labels_by_roles(db, roles))
        ),
        AssetSchema,
    )
