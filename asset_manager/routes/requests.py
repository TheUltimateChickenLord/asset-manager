# pylint: disable=too-many-arguments, too-many-positional-arguments
"""Defines all the routes for requests"""

import json
from fastapi import APIRouter, HTTPException, status

from asset_manager.core.auth import CurrentActiveUser
from asset_manager.core.authz_utils import (
    get_labels_by_roles,
    get_requests_by_labels,
    has_role,
)
from asset_manager.core.logger import log_db_usage
from asset_manager.db.models.request import Request
from asset_manager.db.session import DependsDB
from asset_manager.repositories.asset_repo import AssetRepository
from asset_manager.repositories.request_repo import RequestRepository
from asset_manager.repositories.role_repo import RoleRepository
from asset_manager.routes.assets import asset_exists
from asset_manager.schemas.request import (
    RequestSchema,
    CreateRequestSchema,
    RequestUpdateSchema,
)
from asset_manager.schemas.cast import cast_to_pydantic


router = APIRouter(tags=["Requests"])


def request_exists(request_id: int, repo: RequestRepository) -> Request:
    """Returns whether an request exists or not"""
    request = repo.get_by_id(request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    return request


@router.get("/")
def get_all_requests_to_approve(
    current_user: CurrentActiveUser,
    db: DependsDB,
) -> list[RequestSchema]:
    """Get assignments that the current user can approve"""
    repo = RequestRepository(db)
    role_repo = RoleRepository(db)

    if role_repo.has_scope_all(current_user.id, "CheckInOutAsset"):
        log_db_usage("select", "requests", current_user.email, "Accessed all requests")
        return cast_to_pydantic(repo.get_all(), RequestSchema)

    roles = [
        role.scope for role in role_repo.get_roles(current_user.id, "CheckInOutAsset")
    ]
    if len(roles) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access requests",
        )

    log_db_usage("select", "requests", current_user.email, "Accessed all requests")

    return cast_to_pydantic(
        repo.get_all(subquery=get_requests_by_labels(get_labels_by_roles(db, roles))),
        RequestSchema,
    )


@router.post("/approve/")
def approve_request(
    request: RequestUpdateSchema,
    current_user: CurrentActiveUser,
    db: DependsDB,
) -> RequestSchema:
    """Approve a request for an asset"""
    repo = RequestRepository(db)
    asset_repo = AssetRepository(db)

    request_model = request_exists(request.id, repo)
    if request_model.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot approve request as it already has a status",
        )

    labels = [label.name for label in request_model.asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot approve request",
        )

    asset_repo.update(request_model.asset, {"status": "Reserved"})
    updated_request = repo.update(
        request_model, {"status": "Approved", "approved_by": current_user.id}
    )

    log_db_usage(
        "update",
        "assets",
        current_user.email,
        f"Reserved asset {request_model.asset_id}",
    )
    log_db_usage(
        "update", "requests", current_user.email, f"Approved request {request_model.id}"
    )

    return cast_to_pydantic(updated_request, RequestSchema)


@router.post("/reject/")
def reject_request(
    request: RequestUpdateSchema,
    current_user: CurrentActiveUser,
    db: DependsDB,
) -> RequestSchema:
    """Reject a request for an asset"""
    repo = RequestRepository(db)

    request_model = request_exists(request.id, repo)
    if request_model.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot reject request as it already has a status",
        )

    labels = [label.name for label in request_model.asset.labels]
    if not has_role(current_user, "CheckInOutAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot reject request",
        )

    log_db_usage(
        "update", "requests", current_user.email, f"Rejected request {request_model.id}"
    )

    return cast_to_pydantic(
        repo.update(
            request_model, {"status": "Rejected", "approved_by": current_user.id}
        ),
        RequestSchema,
    )


@router.get("/my/")
def get_my_requests(
    current_user: CurrentActiveUser, db: DependsDB
) -> list[RequestSchema]:
    """Get all my requests that the current user has submitted"""
    repo = RequestRepository(db)
    log_db_usage("select", "requests", current_user.email, "Accessed their requests")
    return cast_to_pydantic(
        repo.get_requests_by_user(current_user.id),
        RequestSchema,
    )


@router.post("/")
def submit_request(
    data: CreateRequestSchema,
    current_user: CurrentActiveUser,
    db: DependsDB,
) -> RequestSchema:
    """Submit a new request"""
    repo = RequestRepository(db)
    asset_repo = AssetRepository(db)

    asset = asset_exists(data.asset_id, asset_repo)

    labels = [label.name for label in asset.labels]
    if not has_role(current_user, "RequestAsset", labels):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot make request",
        )

    log_db_usage(
        "insert",
        "requests",
        current_user.email,
        f"Submitted request with info {json.dumps(data.model_dump(), default=str)}",
    )

    return cast_to_pydantic(
        repo.create({**data.model_dump(), "user_id": current_user.id}), RequestSchema
    )


@router.get("/{request_id}/")
def get_request(
    request_id: int, current_user: CurrentActiveUser, db: DependsDB
) -> RequestSchema:
    """Get a request by its ID"""
    repo = RequestRepository(db)

    request = request_exists(request_id, repo)

    labels = [label.name for label in request.asset.labels]
    if not (
        has_role(current_user, "CheckInOutAsset", labels)
        or request.user_id == current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot get request",
        )

    log_db_usage(
        "select", "requests", current_user.email, f"Accessed request {request.id}"
    )

    return cast_to_pydantic(request, RequestSchema)
