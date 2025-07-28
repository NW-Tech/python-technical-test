# app/routers/group_type.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db import get_session
from app.infrastructure.models.group_type import GroupType

router = APIRouter(prefix="/group_types", tags=["GroupTypes"])


class GroupTypeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class GroupTypeCreate(GroupTypeBase):
    pass


class GroupTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)


class GroupTypeOut(GroupTypeBase):
    id: int

    class Config:
        orm_mode = True


@router.get("/", response_model=List[GroupTypeOut])
async def list_group_types(
    name: Optional[str] = Query(None, description="Filter by name"),
    sort_by: Optional[str] = Query("id", description="Field to sort by"),
    desc: bool = Query(False, description="Sort descending"),
    session: AsyncSession = Depends(get_session),
):
    query = select(GroupType)

    if name:
        query = query.where(GroupType.name.ilike(f"%{name}%"))

    if hasattr(GroupType, sort_by):
        column = getattr(GroupType, sort_by)
        query = query.order_by(column.desc() if desc else column)

    result = await session.execute(query)
    return result.scalars().all()


@router.post("/", response_model=GroupTypeOut, status_code=201)
async def create_group_type(data: GroupTypeCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(select(GroupType).where(GroupType.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="GroupType with this name already exists")

    group_type = GroupType(name=data.name)
    session.add(group_type)
    await session.commit()
    await session.refresh(group_type)
    return group_type


@router.put("/{group_type_id}", response_model=GroupTypeOut)
async def update_group_type(
    group_type_id: int, data: GroupTypeUpdate, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(GroupType).where(GroupType.id == group_type_id))
    group_type = result.scalar_one_or_none()

    if not group_type:
        raise HTTPException(status_code=404, detail="GroupType not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(group_type, key, value)

    await session.commit()
    await session.refresh(group_type)
    return group_type


@router.delete("/{group_type_id}", status_code=204)
async def delete_group_type(group_type_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(GroupType).where(GroupType.id == group_type_id))
    group_type = result.scalar_one_or_none()

    if not group_type:
        raise HTTPException(status_code=404, detail="GroupType not found")

    await session.delete(group_type)
    await session.commit()
