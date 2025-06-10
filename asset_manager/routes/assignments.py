# pylint: disable=too-many-arguments, too-many-positional-arguments
"""Defines all the routes for asset assignments"""

from datetime import date, datetime, timedelta, timezone
import json

from fastapi import APIRouter, HTTPException, Query, status

from asset_manager.core.auth import CurrentActiveUser
from asset_manager.core.authz_utils import has_role
from asset_manager.core.logger import log_db_usage
from asset_manager.db.session import DependsDB
from asset_manager.repositories.asset_repo import AssetRepository
from asset_manager.repositories.assignment_repo import AssetAssignmentRepository
from asset_manager.repositories.request_repo import RequestRepository
from asset_manager.routes.assets import asset_exists
from asset_manager.routes.requests import request_exists
from asset_manager.schemas.assignments import (
    AssetAssignmentSchema,
    CheckInAssetSchema,
    CheckOutAssetRequestSchema,
    CheckOutAssetSchema,
    RequestReturnSchema,
)
from asset_manager.schemas.cast import cast_to_pydantic


router = APIRouter(tags=["Assignments"])


@router.post("/check-in/", tags=["Assets"])
def check_in_asset_by_asset_id(
    data: CheckInAssetSchema, db: DependsDB, current_user: CurrentActiveUser
) -> AssetAssignmentSchema:
    """Check in an item in the database"""
    assignment_repo = AssetAssignmentRepository(db)
    asset_repo = AssetRepository(db)

    asset = asset_exists(data.asset_id, asset_repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot check in asset",
        )

    assignment = assignment_repo.get_asset_assignment(data.asset_id)
    if asset.status != "In Use" or assignment is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Asset is not checked out"
        )

    asset_repo.update(asset, {"status": "Available"})
    log_db_usage(
        "update",
        "assets",
        current_user.email,
        f"Updated asset {asset.id} status to 'Available'",
    )
    log_db_usage(
        "update",
        "asset_assignments",
        current_user.email,
        f"Updated asset assignment {assignment.id} returned_at",
    )

    return cast_to_pydantic(
        assignment_repo.update(assignment, {"returned_at": datetime.now(timezone.utc)}),
        AssetAssignmentSchema,
    )


@router.post("/check-in/{asset_assignment_id}/", tags=["Assets"])
def check_in_asset_by_assignment_id(
    asset_assignment_id: int, db: DependsDB, current_user: CurrentActiveUser
) -> AssetAssignmentSchema:
    """Check in an item in the database"""
    assignment_repo = AssetAssignmentRepository(db)
    asset_repo = AssetRepository(db)

    assignment = assignment_repo.get_by_id(asset_assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Asset is not checked out"
        )

    labels = [label.name for label in assignment.asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot check in asset",
        )

    if assignment.asset.status != "In Use":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Asset is not checked out"
        )

    asset_repo.update(assignment.asset, {"status": "Available"})
    log_db_usage(
        "update",
        "assets",
        current_user.email,
        f"Updated asset {assignment.asset.id} status to 'Available'",
    )
    log_db_usage(
        "update",
        "asset_assignments",
        current_user.email,
        f"Updated asset assignment {assignment.id} returned_at",
    )

    return cast_to_pydantic(
        assignment_repo.update(assignment, {"returned_at": datetime.now(timezone.utc)}),
        AssetAssignmentSchema,
    )


@router.post("/check-out/", tags=["Assets"])
def check_out_asset(
    data: CheckOutAssetSchema, current_user: CurrentActiveUser, db: DependsDB
) -> AssetAssignmentSchema:
    """Check out an item in the database"""
    assignment_repo = AssetAssignmentRepository(db)
    asset_repo = AssetRepository(db)

    asset = asset_exists(data.asset_id, asset_repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot check out asset",
        )

    if asset.status != "Available":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Asset status is not available"
        )

    asset_repo.update(asset, {"status": "In Use"})
    assignment = assignment_repo.check_out_asset(
        asset, data.user_id, current_user.id, data.due_in_days
    )
    log_db_usage(
        "update",
        "assets",
        current_user.email,
        f"Updated asset {asset.id} status to 'In Use'",
    )
    log_db_usage(
        "insert",
        "asset_assignmentss",
        current_user.email,
        f"Created asset assignment {assignment.id} with info {json.dumps(data, default=str)}",
    )

    return cast_to_pydantic(
        assignment,
        AssetAssignmentSchema,
    )


@router.post("/check-out/{request_id}/", tags=["Assets"])
def check_out_request(
    request_id: int,
    data: CheckOutAssetRequestSchema,
    current_user: CurrentActiveUser,
    db: DependsDB,
) -> AssetAssignmentSchema:
    """Check out an item in the database"""
    assignment_repo = AssetAssignmentRepository(db)
    asset_repo = AssetRepository(db)
    request_repo = RequestRepository(db)

    request = request_exists(request_id, request_repo)

    labels = [label.name for label in request.asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot check out asset",
        )

    if request.asset.status != "Reserved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Asset status is not available"
        )

    asset_repo.update(request.asset, {"status": "In Use"})
    request_repo.update(request, {"status": "Fulfilled"})
    assignment = assignment_repo.check_out_asset_request(
        request, current_user.id, data.due_in_days
    )
    log_db_usage(
        "update",
        "assets",
        current_user.email,
        f"Updated asset {request.asset.id} status to 'In Use'",
    )
    log_db_usage(
        "update",
        "requests",
        current_user.email,
        f"Updated request {request.id} status to 'Fulfilled'",
    )
    log_db_usage(
        "insert",
        "asset_assignmentss",
        current_user.email,
        f"Created asset assignment {assignment.id} with info {json.dumps(data, default=str)}",
    )

    return cast_to_pydantic(
        assignment,
        AssetAssignmentSchema,
    )


@router.get("/my/")
def get_my_assignments(
    current_user: CurrentActiveUser,
    db: DependsDB,
) -> list[AssetAssignmentSchema]:
    """Get all assets assigned to the current user"""
    repo = AssetAssignmentRepository(db)
    log_db_usage(
        "select",
        "asset_assignments",
        current_user.email,
        "Accessed all assignments related to them",
    )
    return cast_to_pydantic(repo.get_by_user(current_user.id), AssetAssignmentSchema)


@router.put("/request-return/")
def request_assignment_return(
    data: RequestReturnSchema, db: DependsDB, current_user: CurrentActiveUser
) -> AssetAssignmentSchema:
    """Update the return date for an asset"""
    repo = AssetAssignmentRepository(db)

    asset_assignment = repo.get_by_id(data.asset_assignment_id)
    if asset_assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset assignment not found"
        )

    labels = [label.name for label in asset_assignment.asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot request asset return",
        )

    due_date = date.today() + timedelta(days=data.due_in_days)
    log_db_usage(
        "update",
        "asset_assignments",
        current_user.email,
        f"Updated return date of {asset_assignment.id} to {due_date.isoformat()}",
    )

    return cast_to_pydantic(
        repo.update(asset_assignment, {"due_date": due_date}), AssetAssignmentSchema
    )


@router.get("/overdue/", tags=["Assets"])
def get_overdue(
    current_user: CurrentActiveUser,
    db: DependsDB,
    due_in_days: int = Query(0, gte=0),
) -> list[AssetAssignmentSchema]:
    """Get all overdue assets for the current user"""
    repo = AssetAssignmentRepository(db)
    log_db_usage(
        "select",
        "asset_assignments",
        current_user.email,
        f"Accessed all assignments due in the next {due_in_days} days related to them",
    )
    return cast_to_pydantic(
        repo.get_overdue(current_user.id, due_in_days), AssetAssignmentSchema
    )


@router.get("/{assignment_id}/")
def get_assignment_by_id(
    assignment_id: int,
    current_user: CurrentActiveUser,
    db: DependsDB,
) -> AssetAssignmentSchema:
    """Get all assets assigned to the current user"""
    repo = AssetAssignmentRepository(db)

    assignment = repo.get_by_id(assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    if not (current_user.id in {assignment.user_id, assignment.assigned_by_id}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot get assignment",
        )

    log_db_usage(
        "select",
        "asset_assignments",
        current_user.email,
        f"Accessed assignment with id {assignment_id}",
    )
    return cast_to_pydantic(assignment, AssetAssignmentSchema)
