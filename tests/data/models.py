from sqlalchemy.orm import Mapped, mapped_column
from asset_manager.db.base import Base


class DummyModelSoftDelete(Base):
    __tablename__ = "dummy_soft"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    is_deleted: Mapped[bool] = mapped_column(default=False)


class DummyModelHardDelete(Base):
    __tablename__ = "dummy_hard"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
