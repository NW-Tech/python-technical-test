from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.db import Base
from app.infrastructure.models.associations import site_group_association


class Site(Base):
    """
    Represents a physical site or installation.

    Attributes:
        id (int): Unique identifier.
        name (str): Site name.
        installation_date (date): Date of site installation.
        max_power_megawatt (float): Max capacity.
        min_power_megawatt (float): Min capacity.
        useful_energy_at_1_megawatt (float): Performance indicator.

    Relationships:
        groups: Many-to-many relationship with groups.
    """

    __tablename__ = "sites"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    installation_date = Column(Date, nullable=False)
    max_power_megawatt = Column(Float, nullable=False)
    min_power_megawatt = Column(Float, nullable=False)
    useful_energy_at_1_megawatt = Column(Float, nullable=True)
    efficiency = Column(Float, nullable=True)
    country = Column(String, nullable=False)

    groups = relationship("Group", secondary=site_group_association, back_populates="sites")

    @property
    def group_ids(self):
        return [g.id for g in self.groups] if self.groups else []
