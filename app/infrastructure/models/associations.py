from sqlalchemy import Column, ForeignKey, Table

from app.infrastructure.db import Base

# Relacionamento Site <-> Group (muitos para muitos)
site_group_association = Table(
    "site_group_association",
    Base.metadata,
    Column("site_id", ForeignKey("sites.id"), primary_key=True),
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
    extend_existing=True,
)


# Relacionamento recursivo Group <-> Group (muitos para muitos)
group_group_association = Table(
    "group_group_association",
    Base.metadata,
    Column("parent_group_id", ForeignKey("groups.id"), primary_key=True),
    Column("child_group_id", ForeignKey("groups.id"), primary_key=True),
    extend_existing=True,
)
