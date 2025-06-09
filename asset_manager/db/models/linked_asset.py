# pylint: disable=too-few-public-methods
"""Module defining all the LinkedAsset model"""

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from asset_manager.db.base import Base


class LinkedAsset(Base):
    """SQLAlchemy LinkedAsset model for the db"""

    __tablename__ = "linked_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    linked_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    relation: Mapped[str] = mapped_column(
        CheckConstraint("relation IN ('License', 'Consumable', 'Peripheral')")
    )

    asset = relationship(
        "Asset", back_populates="linked_assets", foreign_keys=[asset_id]
    )
    linked_asset = relationship(
        "Asset", back_populates="linked_to", foreign_keys=[linked_id]
    )
