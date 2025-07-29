# ruff: noqa: B008

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dependencies.security import get_current_user
from app.infrastructure.db import get_session
from app.infrastructure.models.group import Group

router = APIRouter(prefix="/groups", tags=["Groups"])


class GroupBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type_id: int = Field(..., description="ID of the associated GroupType")


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: str = Field(None, min_length=2, max_length=100)
    type_id: int


class GroupOut(GroupBase):
    id: int

    class Config:
        from_attributes = True


@router.get("/", response_model=list[GroupOut])
async def list_groups(
    name: str = Query(None, description="Filter by group name"),
    sort_by: str = Query("id", description="Sort field"),
    desc: bool = Query(False, description="Descending sort"),
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    query = select(Group)

    if name:
        query = query.where(Group.name.ilike(f"%{name}%"))

    if hasattr(Group, sort_by):
        sort_column = getattr(Group, sort_by)
        if desc:
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

    result = await session.execute(query)
    return result.scalars().all()


@router.post("/", response_model=GroupOut, status_code=201)
async def create_group(
    data: GroupCreate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    group = Group(**data.dict())
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


@router.put("/{group_id}", response_model=GroupOut)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(group, key, value)

    await session.commit()
    await session.refresh(group)
    return group


@router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await session.delete(group)
    await session.commit()
