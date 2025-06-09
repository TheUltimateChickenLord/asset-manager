# pylint: disable=too-few-public-methods
"""Module defining all the LabelMapping models"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from asset_manager.db.base import Base


class LabelMappingUser(Base):
    """SQLAlchemy LabelMappingUser model for the db"""

    __tablename__ = "label_mapping_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    label_id: Mapped[int] = mapped_column(ForeignKey("labels.id"))


class LabelMappingAsset(Base):
    """SQLAlchemy LabelMappingAsset model for the db"""

    __tablename__ = "label_mapping_asset"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    label_id: Mapped[int] = mapped_column(ForeignKey("labels.id"))
