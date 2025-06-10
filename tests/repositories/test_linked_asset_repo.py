"""Test module for LinkedAssetRepository"""

import pytest

from sqlalchemy.orm import Session

from asset_manager.db import session
from asset_manager.db.base import Base
from asset_manager.db.models import *
from asset_manager.repositories.linked_asset_repo import LinkedAssetRepository
from tests.data.model_creators import create_asset
from tests.data.reload import reload_all_modules


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch: pytest.MonkeyPatch):
    """Fixture set the database to in-memory for testing"""
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("LOG_DIR", "tests/logs")
    reload_all_modules()


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to create a new database session for testing
    Automatically tears down the schema after each test
    """
    current_session = session.SessionLocal()
    Base.metadata.create_all(bind=session.engine)
    yield current_session
    current_session.close()
    Base.metadata.drop_all(bind=session.engine)


class TestLinkedAssetRepository:
    """Test suite for LinkedAssetRepository"""

    def test_link_assets_and_retrieve_all(self, db_session: Session):
        """Test linking assets and retrieving linked list by asset_id"""
        linked_asset_repo = LinkedAssetRepository(db_session)
        printer = create_asset(db_session, name="Printer")
        toner = create_asset(db_session, name="Toner")
        paper = create_asset(db_session, name="Paper")

        linked_asset_repo.create(
            {"asset_id": printer.id, "linked_id": toner.id, "relation": "Consumable"}
        )
        linked_asset_repo.create(
            {"asset_id": printer.id, "linked_id": paper.id, "relation": "Consumable"}
        )

        links = linked_asset_repo.get_linked_assets(printer.id)
        assert len(links) == 2
        assert all(link.asset_id == printer.id for link in links)

    def test_get_specific_link(self, db_session: Session):
        """Test get_link() returns the specific asset-to-asset link"""
        linked_asset_repo = LinkedAssetRepository(db_session)
        computer = create_asset(db_session, name="Laptop")
        mouse = create_asset(db_session, name="Mouse")

        linked_asset_repo.create(
            {"asset_id": computer.id, "linked_id": mouse.id, "relation": "Peripheral"}
        )
        found = linked_asset_repo.get_link(computer.id, mouse.id)

        assert found is not None
        assert found.relation == "Peripheral"
        assert found.asset_id == computer.id
        assert found.linked_id == mouse.id

    def test_get_link_returns_none_if_not_linked(self, db_session: Session):
        """Test get_link() returns None when no such link exists"""
        linked_asset_repo = LinkedAssetRepository(db_session)
        a1 = create_asset(db_session, name="Router")
        a2 = create_asset(db_session, name="Switch")

        result = linked_asset_repo.get_link(a1.id, a2.id)
        assert result is None
