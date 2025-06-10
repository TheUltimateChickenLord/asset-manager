"""Module defining utility functions for authorization"""

from typing import Iterable
from sqlalchemy import ColumnElement, exists, select
from sqlalchemy.orm import Session

from asset_manager.db.models.asset import Asset
from asset_manager.db.models.label import Label
from asset_manager.db.models.label_mapping import LabelMappingAsset, LabelMappingUser
from asset_manager.db.models.request import Request
from asset_manager.db.models.role import Role
from asset_manager.db.models.user import User


def get_assets_by_labels(labels: list[int]) -> ColumnElement[bool]:
    """Get all the assets that fit a set of labels"""
    subq = select(LabelMappingAsset.item_id).where(
        LabelMappingAsset.item_id == Asset.id,
        LabelMappingAsset.label_id.notin_(labels),
    )

    return ~exists(subq)


def get_users_by_labels(labels: list[int]) -> ColumnElement[bool]:
    """Get all the assets that fit a set of labels"""
    subq = select(LabelMappingUser.item_id).where(
        LabelMappingUser.item_id == User.id,
        LabelMappingUser.label_id.notin_(labels),
    )

    return ~exists(subq)


def get_requests_by_labels(labels: list[int]) -> ColumnElement[bool]:
    """Get all the assets that fit a set of labels"""
    subq = select(LabelMappingAsset.item_id).where(
        Request.asset.has(id=LabelMappingAsset.item_id),
        LabelMappingAsset.label_id.notin_(labels),
    )

    return ~exists(subq)


def get_labels_by_roles(db: Session, roles: Iterable[str]) -> list[int]:
    """Get all the assets that fit a set of labels"""
    labels = db.query(Label.id).filter(Label.name.in_(roles)).all()
    return [label[0] for label in labels]


def has_role(user: User, role: str, labels: Iterable[str]) -> bool:
    """Checks if the user has the role for the labels"""
    roles_list: list[Role] = user.roles
    scopes: set[str] = set()
    for role_obj in roles_list:
        if role_obj.role == role:
            scopes.add(role_obj.scope)

    return "*" in scopes or all(label in scopes for label in labels)
