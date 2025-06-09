# pylint: disable=too-few-public-methods
"""Module defining all the Request model"""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from asset_manager.db.base import Base


class Request(Base):
    """SQLAlchemy Request model for the db"""

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    status: Mapped[str] = mapped_column(
        CheckConstraint("status IN ('Pending', 'Approved', 'Rejected', 'Fulfilled')"),
        default="Pending",
    )
    justification: Mapped[str]
    requested_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    user = relationship("User", back_populates="requests", foreign_keys=[user_id])
    approver = relationship(
        "User", back_populates="approvals", foreign_keys=[approved_by]
    )
    asset = relationship("Asset", back_populates="requests")
    assignment = relationship(
        "AssetAssignment", back_populates="request", uselist=False
    )
