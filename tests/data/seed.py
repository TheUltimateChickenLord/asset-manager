"""Script to seed the database with template data"""

from datetime import date, timedelta

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from asset_manager.core.security import hash_password
from asset_manager.db.models.label_mapping import LabelMappingAsset, LabelMappingUser
from asset_manager.db.models.user import User
from asset_manager.db.session import SessionLocal, engine
from asset_manager.db.base import Base
from asset_manager.db.models.asset import Asset
from asset_manager.db.models.label import Label


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
    # Seed Assets
    assets = seed_assets()
    session.add_all(assets)
    session.commit()
    # Seed Labels
    labels = seed_labels()
    session.add_all(labels)
    session.commit()
    # Seed Label Mappings Assets
    session.add_all(seed_label_mappings_asset(assets, labels))
    session.commit()
    # Seed Label Mappings Users
    session.add_all(seed_label_mappings_user(users, labels))
    session.commit()


def seed_users():
    """Function to create random seed users"""
    users: list[User] = []
    for i in range(10):
        pw_hash, salt = hash_password("Password123!")
        users.append(
            User(
                name=f"User {i}",
                email=f"user{i}@example.com",
                password_hash=pw_hash,
                password_salt=salt,
                reset_password=False,
            )
        )
    return users


def seed_assets():
    """Function to create random seed assets"""
    return [
        Asset(
            asset_tag=f"AST-{i}",
            name=f"Asset{i}",
            description=f"Fake desc {i}",
            status=["Available", "In Use", "Maintenance"][i % 3],
            purchase_date=date.today() - timedelta(days=i),
            purchase_cost=10 * i,
            maintenance_rate=10 * i,
        )
        for i in range(10)
    ]


def seed_labels():
    """Function to create random seed labels"""
    return [
        Label(name="department:HR"),
        Label(name="department:IT"),
        Label(name="location:Lon"),
        Label(name="location:Man"),
    ]


def seed_label_mappings_asset(assets: list[Asset], labels: list[Label]):
    """Function to create random seed label mappings for assets"""
    mappings = [
        LabelMappingAsset(
            item_id=assets[asset].id,
            label_id=labels[label].id,
        )
        for asset in range(10)
        for label in range(3)
        if asset % (label + 2) == 0
    ]
    return mappings


def seed_label_mappings_user(users: list[User], labels: list[Label]):
    """Function to create random seed label mappings for users"""
    mappings = [
        LabelMappingUser(
            item_id=users[user].id,
            label_id=labels[label].id,
        )
        for user in range(10)
        for label in range(3)
        if user % (label + 2) == 0
    ]
    return mappings
