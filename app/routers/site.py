from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db import get_session
from app.infrastructure.models.site import Site

router = APIRouter(prefix="/sites", tags=["Sites"])


class SiteCreate(BaseModel):
    name: str
    installation_date: str
    max_power_megawatt: float
    min_power_megawatt: float
    useful_energy_at_1_megawatt: float


class SiteUpdate(SiteCreate):
    pass


class SiteOut(SiteCreate):
    id: int

    class Config:
        orm_mode = True


@router.get("/", response_model=List[SiteOut])
async def list_sites(
    name: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("id"),
    desc: bool = Query(False),
    session: AsyncSession = Depends(get_session),
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
async def create_site(data: SiteCreate, session: AsyncSession = Depends(get_session)):
    site = Site(**data.dict())
    session.add(site)
    await session.commit()
    await session.refresh(site)
    return site


@router.put("/{site_id}", response_model=SiteOut)
async def update_site(site_id: int, data: SiteUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(site, key, value)
    await session.commit()
    await session.refresh(site)
    return site


@router.delete("/{site_id}")
async def delete_site(site_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await session.delete(site)
    await session.commit()
    return {"detail": f"Site {site_id} deleted"}
