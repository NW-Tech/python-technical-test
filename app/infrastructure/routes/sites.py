from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from infrastructure.db import get_session
from infrastructure.models import FrenchSite, Group, ItalianSite, Site
from pydantic import BaseModel, validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

SESSION_DEPEND = Depends(get_session)
NONE_QUERY = Query(None)


class SiteBase(BaseModel):
    name: str
    installation_date: date
    max_power_megawatt: float
    min_power_megawatt: float
    country: str
    group_ids: list[int] | None = None


class SiteCreate(SiteBase):
    useful_energy_at_1_megawatt: float | None = None
    efficiency: float | None = None
    country: str = ""

    @validator("country")
    @classmethod
    def country_must_be_supported(cls, v):
        if v.lower() not in ("france", "italy"):
            raise ValueError("Unsupported country. Only 'france' and 'italy' are allowed.")
        return v.lower()


class SiteUpdate(BaseModel):
    name: str | None = None
    installation_date: date | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    useful_energy_at_1_megawatt: float | None = None
    efficiency: float | None = None
    group_ids: list[int] | None = None


def get_site_model(country: str):
    if country == "france":
        return FrenchSite
    elif country == "italy":
        return ItalianSite
    return Site


# create site
@router.post("/sites", response_model=dict)
async def create_site(site: SiteCreate, session: AsyncSession = SESSION_DEPEND):
    if site.country == "france":
        if site.useful_energy_at_1_megawatt is None:
            raise HTTPException(
                status_code=400, detail="French sites require 'useful_energy_at_1_megawatt'."
            )
        # one french site per day
        stmt = select(Site).where(
            Site.country == "france", Site.installation_date == site.installation_date
        )
        result = await session.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=400, detail="A French site is already installed for this day."
            )
    elif site.country == "italian":
        if site.efficiency is None:
            raise HTTPException(status_code=400, detail="Italian sites require 'efficiency'.")
        # italian install on weekends
        if site.installation_date.weekday() not in (5, 6):
            raise HTTPException(
                status_code=400, detail="Italian sites must be installed on weekends."
            )
    else:
        raise HTTPException(status_code=400, detail="Unsupported country.")

    base_kwargs = {
        "name": site.name,
        "installation_date": site.installation_date,
        "max_power_megawatt": site.max_power_megawatt,
        "min_power_megawatt": site.min_power_megawatt,
        "country": site.country,
    }
    if site.country == "france":
        base_kwargs["useful_energy_at_1_megawatt"] = site.useful_energy_at_1_megawatt
        sitemodel = FrenchSite
    elif site.country == "italian":
        base_kwargs["efficiency"] = site.efficiency
        sitemodel = ItalianSite

    new_site = sitemodel(**base_kwargs)

    if site.group_ids:
        stmt = select(Group).where(Group.id.in_(site.group_ids))
        result = await session.execute(stmt)
        groups = result.scalars().all()
        for g in groups:
            if g.type.value == "group3":
                raise HTTPException(
                    status_code=400, detail="Cannot associate site with a group of type 'group3'."
                )
        new_site.groups = groups

    session.add(new_site)
    await session.commit()
    return {"id": new_site.id, "message": "Site created successfully"}


# retrieve sites
@router.get("/sites", response_model=list[dict])
async def get_sites(
    name: str | None = NONE_QUERY,
    installation_date: date | None = NONE_QUERY,
    session: AsyncSession = SESSION_DEPEND,
):
    selected_site = select(Site)
    if name:
        selected_site = selected_site.where(Site.name.ilike(f"%{name}%"))
    if installation_date:
        selected_site = selected_site.where(Site.installation_date == installation_date)
    result = await session.execute(selected_site)
    sites = result.scalars().all()
    response = []
    for s in sites:
        response.append(
            {
                "id": s.id,
                "name": s.name,
                "installation_date": s.installation_date,
                "max_power_megawatt": s.max_power_megawatt,
                "min_power_megawatt": s.min_power_megawatt,
                "country": s.country,
                "useful_energy_at_1_megawatt": getattr(s, "useful_energy_at_1_megawatt", None),
                "efficiency": getattr(s, "efficiency", None),
                "group_ids": [g.id for g in s.groups],
            }
        )
    return response


# update site
@router.patch("/sites/{site_id}", response_model=dict)
async def update_site(site_id: int, site: SiteUpdate, session: AsyncSession = SESSION_DEPEND):
    stmt = select(Site).where(Site.id == site_id)
    result = await session.execute(stmt)
    existing_site = result.scalars().first()
    if not existing_site:
        raise HTTPException(status_code=404, detail="Site not found.")

    update_data = site.model_dump(exclude_unset=True)
    if "installation_date" in update_data:
        if existing_site.country == "france":
            stmt = select(Site).where(
                Site.country == "france",
                Site.installation_date == update_data["installation_date"],
                Site.id != site_id,
            )
            result = await session.execute(stmt)
            if result.scalars().first():
                raise HTTPException(
                    status_code=400, detail="A French site is already installed for this day."
                )
        elif existing_site.country == "italy":
            if update_data["installation_date"].weekday() not in (5, 6):
                raise HTTPException(
                    status_code=400, detail="Italian sites must be installed on weekends."
                )

    # validate update on group associations
    if "group_ids" in update_data:
        stmt = select(Group).where(Group.id.in_(update_data["group_ids"]))
        result = await session.execute(stmt)
        groups = result.scalars().all()
        for g in groups:
            if g.type.value == "group3":
                raise HTTPException(
                    status_code=400, detail="Cannot associate site with a group of type 'group3'."
                )
        existing_site.groups = groups
        update_data.pop("group_ids")

    for key, value in update_data.items():
        setattr(existing_site, key, value)

    await session.commit()
    return {"message": "Site updated successfully"}


# delete site
@router.delete("/sites/{site_id}", response_model=dict)
async def delete_site(site_id: int, session: AsyncSession = SESSION_DEPEND):
    stmt = delete(Site).where(Site.id == site_id)
    await session.execute(stmt)
    await session.commit()
    return {"message": "Site deleted successfully"}
