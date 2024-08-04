#!/usr/bin/env python3

from sqlalchemy.schema import Column
from sqlalchemy.types import String

from . import Base


class Tahp(Base):
    """
    Let tahp cook =)))
    """

    __tablename__ = 'tahp'

    task = Column(
        String,
        primary_key=True)

    data = Column(
        String,
        nullable=False)