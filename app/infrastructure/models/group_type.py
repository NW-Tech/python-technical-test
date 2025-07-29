from sqlalchemy import Boolean, Column, Integer, String
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

    The `can_be_associated_with_site` field controls whether
    groups of this type can be associated with sites.
    """

    __tablename__ = "group_types"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    can_be_associated_with_site = Column(Boolean, nullable=False, default=True)

    groups = relationship("Group", back_populates="type")
