from typing import ClassVar

from infrastructure.db import Base
from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.orm import relationship


class Site(Base):
    __tablename__ = "site"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    installation_date = Column(Date, nullable=False)
    max_power_megawatt = Column(Float, nullable=False)
    min_power_megawatt = Column(Float, nullable=False)
    country = Column(String, nullable=False)

    __mapper_args__: ClassVar[dict] = {"polymorphic_on": country, "polymorphic_identity": "generic"}

    # site_group defined in __init__.py
    groups = relationship("Group", secondary="site_group", back_populates="sites")


class FrenchSite(Site):
    __mapper_args__: ClassVar[dict] = {"polymorphic_identity": "france"}
    useful_energy_at_1_megawatt = Column(Float, nullable=True)


class ItalianSite(Site):
    __mapper_args__: ClassVar[dict] = {"polymorphic_identity": "italy"}
    efficiency = Column(Float, nullable=True)
