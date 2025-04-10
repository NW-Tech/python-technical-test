from fastapi import APIRouter, Depends, HTTPException, Query
from infrastructure.db import get_session
from infrastructure.models import Group, GroupType, Site
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

SESSION_DEPEND = Depends(get_session)
NONE_QUERY = Query(None)


class GroupBase(BaseModel):
    name: str
    type: GroupType


class GroupCreate(GroupBase):
    site_ids: list[int] | None = None
    child_group_ids: list[int] | None = None


class GroupUpdate(BaseModel):
    name: str | None = None
    type: GroupType | None = None
    site_ids: list[int] | None = None
    child_group_ids: list[int] | None = None


# create group
@router.post("/groups", response_model=dict)
async def create_group(group: GroupCreate, session: AsyncSession = SESSION_DEPEND):
    new_group = Group(name=group.name, type=group.type)

    if group.site_ids:

        stmt = select(Site).where(Site.id.in_(group.site_ids))
        result = await session.execute(stmt)
        sites = result.scalars().all()
        # prevent type group3
        if new_group.type.value == "group3" and sites:
            raise HTTPException(
                status_code=400, detail="Cannot associate sites with a group of type 'group3'."
            )
        new_group.sites = sites

    # link child groups if provided
    if group.child_group_ids:
        stmt = select(Group).where(Group.id.in_(group.child_group_ids))
        result = await session.execute(stmt)
        child_groups = result.scalars().all()
        new_group.contained_groups = child_groups

    session.add(new_group)
    await session.commit()
    return {"id": new_group.id, "message": "Group created successfully"}


# retrieve groups
@router.get("/groups", response_model=list[dict])
async def get_groups(
    name: str | None = NONE_QUERY,
    group_type: GroupType | None = NONE_QUERY,
    session: AsyncSession = SESSION_DEPEND,
):
    stmt = select(Group)
    if name:
        stmt = stmt.where(Group.name.ilike(f"%{name}%"))
    if group_type:
        stmt = stmt.where(Group.type == group_type)
    result = await session.execute(stmt)
    groups = result.scalars().all()
    response = []
    for g in groups:
        response.append(
            {
                "id": g.id,
                "name": g.name,
                "type": g.type.value,
                "site_ids": [s.id for s in g.sites],
                "child_group_ids": [cg.id for cg in g.contained_groups],
            }
        )
    return response


# update group
@router.patch("/groups/{group_id}", response_model=dict)
async def update_group(group_id: int, group: GroupUpdate, session: AsyncSession = SESSION_DEPEND):
    stmt = select(Group).where(Group.id == group_id)
    result = await session.execute(stmt)
    existing_group = result.scalars().first()
    if not existing_group:
        raise HTTPException(status_code=404, detail="Group not found.")

    update_data = group.model_dump(exclude_unset=True)

    # check no site linked if modification to group3
    if "type" in update_data and update_data["type"].value == "group3":
        if existing_group.sites:
            raise HTTPException(
                status_code=400,
                detail="Cannot change group type to 'group3' when associated sites exist.",
            )

    if "name" in update_data:
        existing_group.name = update_data["name"]
    if "type" in update_data:
        existing_group.type = update_data["type"]

    if "site_ids" in update_data:

        stmt = select(Site).where(Site.id.in_(update_data["site_ids"]))
        result = await session.execute(stmt)
        sites = result.scalars().all()
        if existing_group.type.value == "group3" and sites:
            raise HTTPException(
                status_code=400, detail="Cannot associate sites with a group of type 'group3'."
            )
        existing_group.sites = sites

    if "child_group_ids" in update_data:
        stmt = select(Group).where(Group.id.in_(update_data["child_group_ids"]))
        result = await session.execute(stmt)
        child_groups = result.scalars().all()
        existing_group.contained_groups = child_groups

    await session.commit()
    return {"message": "Group updated successfully"}


# delete group
@router.delete("/groups/{group_id}", response_model=dict)
async def delete_group(group_id: int, session: AsyncSession = SESSION_DEPEND):
    stmt = delete(Group).where(Group.id == group_id)
    await session.execute(stmt)
    await session.commit()
    return {"message": "Group deleted successfully"}
