# pylint: disable=too-few-public-methods
"""Module defining all the Role model"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from asset_manager.db.base import Base


class Role(Base):
    """SQLAlchemy Role model for the db"""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    scope: Mapped[str]
    role: Mapped[str]

    user = relationship("User", back_populates="roles")
