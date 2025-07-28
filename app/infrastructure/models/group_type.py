from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.db import Base


class GroupType(Base):
    """
    Represents a dynamic group type stored in the database.

    Examples:
        - group1
        - group2
        - group3
        - ...

    This replaces the fixed enum and allows flexible grouping logic
    without needing to redeploy code when a new type is introduced.
    """

    __tablename__ = "group_types"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    groups = relationship("Group", back_populates="type")
