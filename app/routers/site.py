from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    useful_energy_at_1_megawatt: Optional[float] = None
    efficiency: Optional[float] = None
    group_ids: Optional[List[int]] = Field(default_factory=list)

    @field_validator("country")
    @classmethod
    def validate_country(cls, v):
        v = v.upper()
        if v not in {"FR", "IT"}:
            raise ValueError("Only 'FR' and 'IT' are supported.")
        return v

    @field_validator("useful_energy_at_1_megawatt", mode="before")
    @classmethod
    def require_fr_field(cls, v, info):
        if info.data.get("country", "").upper() == "FR" and v is None:
            raise ValueError("Field 'useful_energy_at_1_megawatt' is required for France.")
        return v

    @field_validator("efficiency", mode="before")
    @classmethod
    def require_it_field(cls, v, info):
        if info.data.get("country", "").upper() == "IT" and v is None:
            raise ValueError("Field 'efficiency' is required for Italy.")
        return v


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str]
    country: Optional[str]
    installation_date: Optional[datetime]
    max_power_megawatt: Optional[float]
    min_power_megawatt: Optional[float]
    useful_energy_at_1_megawatt: Optional[float]
    efficiency: Optional[float]
    group_ids: Optional[List[int]] = None


class SiteOut(SiteBase):
    id: int

    class Config:
        orm_mode = True


async def validate_group_associations(session: AsyncSession, group_ids: List[int]):
    if not group_ids:
        return

    stmt = select(Group).where(Group.id.in_(group_ids))
    result = await session.execute(stmt)
    groups = result.scalars().all()

    for group in groups:
        if group.type and not group.type.can_be_associated_with_site:
            raise HTTPException(
                status_code=400,
                detail=f"Group '{group.name}' of type '{group.type.name}' cannot be associated with a site.",
            )


@router.get("/", response_model=List[SiteOut])
async def list_sites(
    name: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("id"),
    desc: bool = Query(False),
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    query = select(Site)
    if name:
        query = query.where(Site.name.ilike(f"%{name}%"))
    if hasattr(Site, sort_by):
        sort_column = getattr(Site, sort_by)
        if desc:
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

    result = await session.execute(query)
    return result.scalars().all()


@router.post("/", response_model=SiteOut)
async def create_site(
    data: SiteCreate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    if data.country == "FR":
        stmt = (
            select(func.count())
            .select_from(Site)
            .where(Site.country == "FR", Site.installation_date == data.installation_date.date())
        )
        result = await session.execute(stmt)
        if result.scalar_one() > 0:
            raise HTTPException(
                status_code=400, detail="Only one French site can be installed per day."
            )
    elif data.country == "IT":
        if data.installation_date.weekday() not in (5, 6):
            raise HTTPException(
                status_code=400, detail="Italian sites must be installed on weekends."
            )

    await validate_group_associations(session, data.group_ids)

    site = Site(**data.dict(exclude={"group_ids"}))
    if data.group_ids:
        stmt = select(Group).where(Group.id.in_(data.group_ids))
        result = await session.execute(stmt)
        site.groups = result.scalars().all()

    session.add(site)
    await session.commit()
    await session.refresh(site)
    return site


@router.put("/{site_id}", response_model=SiteOut)
async def update_site(
    site_id: int,
    data: SiteUpdate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    update_data = data.dict(exclude_unset=True)

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
        result = await session.execute(stmt)
        if result.scalar_one() > 0:
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
        result = await session.execute(stmt)
        site.groups = result.scalars().all()

    for key, value in update_data.items():
        if key != "group_ids":
            setattr(site, key, value)

    await session.commit()
    await session.refresh(site)
    return site


@router.delete("/{site_id}")
async def delete_site(
    site_id: int,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await session.delete(site)
    await session.commit()
    return {"detail": f"Site {site_id} deleted"}
