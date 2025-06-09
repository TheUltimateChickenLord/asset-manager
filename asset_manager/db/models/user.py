# pylint: disable=too-few-public-methods
"""Module defining all the User model"""

from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column, relationship

from asset_manager.db.base import Base


class User(Base):
    """SQLAlchemy User model for the db"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    password_salt: Mapped[str]
    is_disabled: Mapped[bool] = mapped_column(default=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    reset_password: Mapped[bool] = mapped_column(default=True)

    roles = relationship("Role", back_populates="user", lazy="joined")
    labels = relationship(
        "Label", secondary="label_mapping_user", back_populates="users", lazy="joined"
    )
    assignments = relationship(
        "AssetAssignment", back_populates="user", foreign_keys="AssetAssignment.user_id"
    )
    assigner_of = relationship(
        "AssetAssignment",
        back_populates="assigned_by",
        foreign_keys="AssetAssignment.assigned_by_id",
    )
    requests = relationship(
        "Request", back_populates="user", foreign_keys="Request.user_id"
    )
    approvals = relationship(
        "Request", back_populates="approver", foreign_keys="Request.approved_by"
    )
