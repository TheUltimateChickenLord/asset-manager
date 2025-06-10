from datetime import datetime, date, timedelta, timezone
from typing import Any
import uuid

from sqlalchemy.orm import Session

from asset_manager.db.models.asset import Asset
from asset_manager.db.models.assignment import AssetAssignment
from asset_manager.db.models.label import Label
from asset_manager.db.models.linked_asset import LinkedAsset
from asset_manager.db.models.request import Request
from asset_manager.db.models.role import Role
from asset_manager.db.models.user import User


def create_asset(db: Session, **kwargs: Any):
    defaults: dict[str, Any] = {
        "asset_tag": f"ASSET-{uuid.uuid4().hex}",
        "name": "Test Asset",
        "description": "Test description",
        "status": "Available",
        "purchase_date": date.today(),
        "purchase_cost": 1000.0,
        "created_at": datetime.now(timezone.utc),
        "last_maintenance": datetime.now(timezone.utc) - timedelta(days=30),
        "maintenance_rate": 30,
        "is_deleted": False,
    }
    defaults.update(kwargs)
    asset = Asset(**defaults)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def create_label(db: Session, **kwargs: Any):
    defaults: dict[str, Any] = {
        "name": f"{uuid.uuid4().hex}",
    }
    defaults.update(kwargs)
    label = Label(**defaults)
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


def create_user(db: Session, **kwargs: Any):
    defaults: dict[str, Any] = {
        "name": f"{uuid.uuid4().hex}",
        "email": f"{uuid.uuid4().hex}@example.com",
        "password_hash": "",
        "password_salt": "",
        "is_disabled": False,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc),
        "reset_password": False,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_request(db: Session, **kwargs: Any):
    defaults: dict[str, Any] = {
        "status": "Pending",
        "justification": "Test justification",
        "requested_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    request = Request(**defaults)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def create_role(db: Session, **kwargs: Any):
    defaults: dict[str, Any] = {"scope": "*", "role": "ReadAsset"}
    defaults.update(kwargs)
    role = Role(**defaults)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def create_assignment(db: Session, **kwargs: Any):
    defaults: dict[str, Any] = {
        "user_id": 2,
        "assigned_by_id": 1,
        "assigned_at": datetime.now(timezone.utc),
        "due_date": date.today(),
    }
    defaults.update(kwargs)
    assignment = AssetAssignment(**defaults)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def create_asset_link(db: Session, **kwargs: Any):
    defaults: dict[str, Any] = {
        "relation": "License",
    }
    defaults.update(kwargs)
    link = LinkedAsset(**defaults)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link
