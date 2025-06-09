# pylint: disable=too-few-public-methods
"""Module defining all the Label model"""

from sqlalchemy.orm import Mapped, mapped_column, relationship

from asset_manager.db.base import Base


class Label(Base):
    """SQLAlchemy Label model for the db"""

    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)

    assets = relationship(
        "Asset", secondary="label_mapping_asset", back_populates="labels"
    )
    users = relationship(
        "User", secondary="label_mapping_user", back_populates="labels"
    )
