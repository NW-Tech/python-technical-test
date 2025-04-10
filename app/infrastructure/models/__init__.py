from infrastructure.db import Base
from infrastructure.models.group import Group, GroupType
from infrastructure.models.site import FrenchSite, ItalianSite, Site
from sqlalchemy import Column, ForeignKey, Integer, Table

# Association tables

site_group = Table(
    "site_group",
    Base.metadata,
    Column("site_id", Integer, ForeignKey("site.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("group.id"), primary_key=True),
)

group_group = Table(
    "group_group",
    Base.metadata,
    Column("parent_id", Integer, ForeignKey("group.id"), primary_key=True),
    Column("child_id", Integer, ForeignKey("group.id"), primary_key=True),
)

__all__ = ["Site", "FrenchSite", "ItalianSite", "Group", "GroupType", "site_group", "group_group"]
