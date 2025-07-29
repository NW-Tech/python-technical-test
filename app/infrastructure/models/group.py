from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.db import Base
from app.infrastructure.models.associations import group_group_association, site_group_association


class Group(Base):
    """
    Represents a logical grouping of sites and/or other groups.

    Attributes:
        id (int): Unique group identifier.
        name (str): Name of the group.
        type_id (int): FK to group_types.id

    Relationships:
        type (GroupType): Type of this group.
        sites (list[Site]): Many-to-many sites in the group.
        children (list[Group]): Sub-groups contained by this group.
        parents (list[Group]): Groups that contain this group.
    """

    __tablename__ = "groups"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    type_id = Column(Integer, ForeignKey("group_types.id"), nullable=False)
    type = relationship("GroupType", back_populates="groups")

    sites = relationship("Site", secondary=site_group_association, back_populates="groups")

    children = relationship(
        "Group",
        secondary=group_group_association,
        primaryjoin=id == group_group_association.c.parent_group_id,
        secondaryjoin=id == group_group_association.c.child_group_id,
        backref="parents",
    )
