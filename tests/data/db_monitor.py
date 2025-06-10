from sqlalchemy.orm import Session

from asset_manager.db.base import Base


def count_elements_in_db(db: Session):
    """Count the total number of rows in the whole db"""
    total = 0
    for tbl in reversed(Base.metadata.sorted_tables):
        total += db.query(tbl).count()

    assert total != 0

    return total
