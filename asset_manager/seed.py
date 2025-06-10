"""Script to seed the database with template data"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from faker import Faker
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from asset_manager.core.security import hash_password
from asset_manager.db.session import SessionLocal, engine
from asset_manager.db.base import Base
from asset_manager.db.models.user import User
from asset_manager.db.models.role import Role
from asset_manager.db.models.asset import Asset
from asset_manager.db.models.linked_asset import LinkedAsset
from asset_manager.db.models.assignment import AssetAssignment
from asset_manager.db.models.request import Request
from asset_manager.db.models.label import Label
from asset_manager.db.models.label_mapping import LabelMappingUser, LabelMappingAsset
from asset_manager.repositories.role_repo import roles


faker = Faker()


def seed():
    """Deletes data in the database and re-seeds it with fake data"""
    session = SessionLocal()
    delete_all(session)
    create_all(session)


def delete_all(session: Session):
    """Deletes everything in the database"""
    for tbl in reversed(Base.metadata.sorted_tables):
        try:
            session.execute(tbl.delete())
        except OperationalError:
            pass


def create_all(session: Session):
    """Create everything in the database"""
    Base.metadata.create_all(engine)
    # Seed Users
    users = seed_users()
    session.add_all(users)
    session.commit()
    # Seed Roles
    session.add_all(seed_roles(users))
    session.commit()
    # Seed Assets
    assets = seed_assets()
    session.add_all(assets)
    session.commit()
    # Seed Linked Assets
    session.add_all(seed_linked_assets(assets))
    session.commit()
    # Seed Requests
    requests = seed_requests(assets, users)
    session.add_all(requests)
    session.commit()
    # Seed Assignments
    session.add_all(seed_assignments(assets, users, requests))
    session.commit()
    # Seed Labels
    labels = seed_labels()
    session.add_all(labels)
    session.commit()
    # Seed Label Mappings Users
    session.add_all(seed_label_mappings_user(users, labels))
    session.commit()
    # Seed Label Mappings Assets
    session.add_all(seed_label_mappings_asset(assets, labels))
    session.commit()

    session.close()


def seed_users():
    """Function to create random seed users"""
    users: list[User] = []
    for _ in range(10):
        pw_hash, salt = hash_password("Password123!")
        users.append(
            User(
                name=faker.name(),
                email=faker.unique.email(),
                password_hash=pw_hash,
                password_salt=salt,
                reset_password=False,
            )
        )
    return users


def seed_roles(users: list[User]):
    """Function to create random seed roles"""
    asset_roles = [role for role in roles if role.endswith("Asset")]
    roles_list: list[Role] = []
    # Full admin roles for user 0
    roles_list.extend(
        Role(
            user_id=users[0].id,
            role=role,
            scope="*",
        )
        for role in roles
    )
    # Manager roles for department:HR for user 1
    roles_list.extend(
        Role(
            user_id=users[1].id,
            role=role,
            scope="department:HR",
        )
        for role in asset_roles
    )
    roles_list.extend(
        Role(
            user_id=users[index].id,
            role=asset,
            scope="department:HR",
        )
        for index in range(2, 10)
        for asset in ["ReadAsset", "RequestAsset"]
    )
    return roles_list


def seed_assets():
    """Function to create random seed assets"""
    return [
        Asset(
            asset_tag=f"AST-{i:03}",
            name=faker.word().capitalize(),
            description=faker.text(),
            status=random.choice(["Available", "In Use", "Maintenance", "Reserved"]),
            purchase_date=faker.date_this_decade(),
            purchase_cost=round(random.uniform(50, 5000), 2),
            maintenance_rate=random.randint(30, 180),
        )
        for i in range(100)
    ]


def seed_linked_assets(assets: list[Asset]):
    """Function to create random seed links between assets"""
    return [
        LinkedAsset(
            asset_id=random.choice(assets).id,
            linked_id=random.choice(assets).id,
            relation=random.choice(["License", "Consumable", "Peripheral"]),
        )
        for _ in range(10)
    ]


def seed_requests(assets: list[Asset], users: list[User]):
    """Function to create random seed requests"""
    requests: list[Request] = []
    available_assets = [asset for asset in assets if asset.status == "Available"]
    for i in range(10):
        reserved_assets = [
            asset
            for asset in assets
            if asset.status == "Reserved"
            and not any(request.asset_id == asset.id for request in requests)
        ]
        in_use_assets = [
            asset
            for asset in assets
            if asset.status == "In Use"
            and not any(request.asset_id == asset.id for request in requests)
        ]
        values: dict[str, Any] = {
            "user_id": random.choice(users[2:]).id,
            "asset_id": random.choice(
                [available_assets, reserved_assets, available_assets, in_use_assets][
                    i % 4
                ]
            ).id,
            "status": ["Pending", "Approved", "Rejected", "Fulfilled"][i % 4],
            "justification": faker.sentence(),
            "approved_by": random.choice(users[:1]).id,
        }
        if values["status"] == "Pending":
            del values["approved_by"]

        requests.append(Request(**values))
    return requests


def seed_assignments(assets: list[Asset], users: list[User], requests: list[Request]):
    """Function to create random seed assignments"""
    fulfilled_requests = [
        request for request in requests if request.status == "Fulfilled"
    ]
    assets = [asset for asset in assets if asset.status == "In Use"]
    random.shuffle(assets)

    assignments: list[AssetAssignment] = []
    for _ in range(10):
        values: dict[str, Any] = {
            "asset_id": assets.pop().id,
            "user_id": random.choice(users[2:]).id,
            "assigned_by_id": random.choice(users[:2]).id,
            "due_date": datetime.now(timezone.utc)
            + timedelta(days=random.randint(14, 60)),
        }

        request = [
            request
            for request in fulfilled_requests
            if request.asset_id == values["asset_id"]
        ]
        if len(request) > 0:
            values["request_id"] = request[0].id

        assignments.append(AssetAssignment(**values))

    return assignments


def seed_labels():
    """Function to create random seed labels"""
    labels = [Label(name=f"department:{faker.unique.word()}") for _ in range(9)]
    labels.append(Label(name="department:HR"))
    return labels


def seed_label_mappings_user(users: list[User], labels: list[Label]):
    """Function to create random seed label mappings for users"""
    return [
        LabelMappingUser(
            item_id=users[user].id,
            label_id=labels[-1].id,
        )
        for user in range(10)
    ]


def seed_label_mappings_asset(assets: list[Asset], labels: list[Label]):
    """Function to create random seed label mappings for asset"""
    return [
        LabelMappingAsset(
            item_id=assets[asset].id,
            label_id=labels[-1].id,
        )
        for asset in range(100)
    ]
