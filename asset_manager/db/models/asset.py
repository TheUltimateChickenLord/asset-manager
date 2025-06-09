# pylint: disable=too-few-public-methods
"""Module defining all the Asset model"""

from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from asset_manager.db.base import Base


class Asset(Base):
    """SQLAlchemy Asset model for the db"""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_tag: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    description: Mapped[str]
    status: Mapped[str] = mapped_column(
        CheckConstraint("status IN ('Available', 'In Use', 'Maintenance', 'Reserved')"),
        default="Available",
    )
    purchase_date: Mapped[date]
    purchase_cost: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    last_maintenance: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    maintenance_rate: Mapped[int]
    is_deleted: Mapped[bool] = mapped_column(default=False)

    assignments = relationship("AssetAssignment", back_populates="asset")
    labels = relationship(
        "Label", secondary="label_mapping_asset", back_populates="assets", lazy="joined"
    )
    requests = relationship("Request", back_populates="asset")
    linked_assets = relationship(
        "LinkedAsset",
        back_populates="asset",
        foreign_keys="LinkedAsset.asset_id",
        lazy="joined",
    )
    linked_to = relationship(
        "LinkedAsset",
        back_populates="linked_asset",
        foreign_keys="LinkedAsset.linked_id",
        lazy="joined",
    )
