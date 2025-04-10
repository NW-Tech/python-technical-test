import enum

from infrastructure.db import Base
from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.orm import relationship


class GroupType(enum.Enum):
    group1 = "group1"
    group2 = "group2"
    group3 = "group3"


class Group(Base):
    __tablename__ = "group"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(GroupType), nullable=False)

    # site_group defined in __init__.py
    sites = relationship("Site", secondary="site_group", back_populates="groups")

    # self reference many-to-many for groups inside groups
    contained_groups = relationship(
        "Group",
        secondary="group_group",
        primaryjoin="Group.id == group_group.c.parent_id",
        secondaryjoin="Group.id == group_group.c.child_id",
        backref="parent_groups",
    )
