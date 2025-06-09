# pylint: disable=too-few-public-methods
"""Module defining all the AssetAssignment model"""

from typing import Optional
from datetime import date, datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from asset_manager.db.base import Base


class AssetAssignment(Base):
    """SQLAlchemy AssetAssignment model for the db"""

    __tablename__ = "asset_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    due_date: Mapped[date]
    returned_at: Mapped[Optional[datetime]]
    request_id: Mapped[Optional[int]] = mapped_column(ForeignKey("requests.id"))

    asset = relationship("Asset", back_populates="assignments", lazy="joined")
    user = relationship("User", back_populates="assignments", foreign_keys=[user_id])
    assigned_by = relationship(
        "User", back_populates="assigner_of", foreign_keys=[assigned_by_id]
    )
    request = relationship("Request", back_populates="assignment", single_parent=True)
