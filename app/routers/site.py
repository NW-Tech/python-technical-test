# ruff: noqa: B008

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies.security import get_current_user
from app.infrastructure.db import get_session
from app.infrastructure.models.group import Group
from app.infrastructure.models.site import Site

router = APIRouter(prefix="/sites", tags=["Sites"])


class SiteBase(BaseModel):
    name: str = Field(..., min_length=2)
    country: str
    installation_date: datetime
    max_power_megawatt: float
    min_power_megawatt: float
    useful_energy_at_1_megawatt: float | None = None
    efficiency: float | None = None
    group_ids: list[int] | None = None

    @field_validator("country", mode="before")
    @classmethod
    def validate_country(cls, v):
        v = v.upper()
        if v not in {"FR", "IT"}:
            raise ValueError("Only 'FR' and 'IT' are supported.")
        return v


class SiteCreate(SiteBase):
    @model_validator(mode="before")
    @classmethod
    def check_required_fields(cls, values: dict):
        country = values.get("country", "").upper()
        if country == "FR" and "useful_energy_at_1_megawatt" not in values:
            raise ValueError("Field 'useful_energy_at_1_megawatt' is required for France.")
        if country == "IT" and "efficiency" not in values:
            raise ValueError("Field 'efficiency' is required for Italy.")
        return values

    @field_validator("useful_energy_at_1_megawatt", mode="before")
    @classmethod
    def require_fr_field(cls, v, info):
        country = info.data.get("country", "").upper()
        if country == "FR" and v is None:
            raise ValueError("Field 'useful_energy_at_1_megawatt' is required for France.")
        return v

    @field_validator("efficiency", mode="before")
    @classmethod
    def require_it_field(cls, v, info):
        country = info.data.get("country", "").upper()
        if country == "IT" and v is None:
            raise ValueError("Field 'efficiency' is required for Italy.")
        return v


class SiteUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    installation_date: datetime | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    useful_energy_at_1_megawatt: float | None = None
    efficiency: float | None = None
    group_ids: list[int] | None = None


class SiteOut(SiteBase):
    id: int

    class Config:
        from_attributes = True


async def validate_group_associations(session: AsyncSession, group_ids: list[int] | None):
    if not group_ids:
        return
    stmt = select(Group).where(Group.id.in_(group_ids)).options(selectinload(Group.type))
    result = await session.execute(stmt)
    groups = result.scalars().all()
    for group in groups:
        if group.type and not group.type.can_be_associated_with_site:
            message = (
                f"Group '{group.name}' of type '{group.type.name}' "
                "cannot be associated with a site."
            )
            raise HTTPException(status_code=400, detail=message)


@router.get("/", response_model=list[SiteOut])
async def list_sites(
    name: str = Query(None),
    sort_by: str = Query("id"),
    desc: bool = Query(False),
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    query = select(Site).options(selectinload(Site.groups))
    if name:
        query = query.where(Site.name.ilike(f"%{name}%"))
    if hasattr(Site, sort_by):
        sort_col = getattr(Site, sort_by)
        if desc:
            sort_col = sort_col.desc()
        query = query.order_by(sort_col)
    result = await session.execute(query)
    sites = result.scalars().all()
    return [
        SiteOut.model_validate(
            {
                **site.__dict__,
                "group_ids": [g.id for g in site.groups] if site.groups else [],
                "id": site.id,
            },
            from_attributes=True,
        )
        for site in sites
    ]


@router.post("/", response_model=SiteOut)
async def create_site(
    data: SiteCreate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    inst_date = (
        data.installation_date.date()
        if isinstance(data.installation_date, datetime)
        else data.installation_date
    )
    if data.country == "FR":
        stmt = (
            select(func.count())
            .select_from(Site)
            .where(Site.country == "FR", Site.installation_date == inst_date)
        )
        count = (await session.execute(stmt)).scalar_one()
        if count > 0:
            raise HTTPException(
                status_code=400, detail="Only one French site can be installed per day."
            )
    elif data.country == "IT":
        dt = data.installation_date
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, datetime.min.time())
        if dt.weekday() not in (5, 6):
            raise HTTPException(
                status_code=400, detail="Italian sites must be installed on weekends."
            )
    await validate_group_associations(session, data.group_ids)
    site = Site(**data.model_dump(exclude={"group_ids"}))
    if data.group_ids:
        stmt = select(Group).where(Group.id.in_(data.group_ids))
        site.groups = (await session.execute(stmt)).scalars().all()
    session.add(site)
    await session.commit()
    site = (
        await session.execute(
            select(Site).options(selectinload(Site.groups)).where(Site.id == site.id)
        )
    ).scalar_one()
    return SiteOut.model_validate(
        {
            **site.__dict__,
            "group_ids": [g.id for g in site.groups] if site.groups else [],
            "id": site.id,
        },
        from_attributes=True,
    )


@router.put("/{site_id}", response_model=SiteOut)
async def update_site(
    site_id: int,
    data: SiteUpdate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    site = (await session.execute(select(Site).where(Site.id == site_id))).scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    update_data = data.model_dump(exclude_unset=True)
    if update_data.get("country") == "FR" and "installation_date" in update_data:
        stmt = (
            select(func.count())
            .select_from(Site)
            .where(
                Site.country == "FR",
                Site.installation_date == update_data["installation_date"].date(),
                Site.id != site_id,
            )
        )
        if (await session.execute(stmt)).scalar_one() > 0:
            raise HTTPException(
                status_code=400, detail="Only one French site can be installed per day."
            )
    if update_data.get("country") == "IT" and "installation_date" in update_data:
        if update_data["installation_date"].weekday() not in (5, 6):
            raise HTTPException(
                status_code=400, detail="Italian sites must be installed on weekends."
            )
    if update_data.get("group_ids") is not None:
        await validate_group_associations(session, update_data["group_ids"])
        stmt = select(Group).where(Group.id.in_(update_data["group_ids"]))
        site.groups = (await session.execute(stmt)).scalars().all()
    for key, value in update_data.items():
        if key != "group_ids":
            setattr(site, key, value)
    await session.commit()
    site = (
        await session.execute(
            select(Site).options(selectinload(Site.groups)).where(Site.id == site.id)
        )
    ).scalar_one()
    return SiteOut.model_validate(
        {
            **site.__dict__,
            "group_ids": [g.id for g in site.groups] if site.groups else [],
            "id": site.id,
        },
        from_attributes=True,
    )


@router.delete("/{site_id}")
async def delete_site(
    site_id: int,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    site = (await session.execute(select(Site).where(Site.id == site_id))).scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await session.delete(site)
    await session.commit()
    return {"detail": f"Site {site_id} deleted"}
