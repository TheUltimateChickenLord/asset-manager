# pylint: disable=too-few-public-methods
"""Module defining all the base class for db models"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all db models"""
