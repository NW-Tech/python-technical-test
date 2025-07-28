import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import select

from app.infrastructure.db import get_session
from app.infrastructure.models.group_type import GroupType

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))


async def seed_group_types():
    async for session in get_session():
        result = await session.execute(select(GroupType))
        existing_names = {row.name for row in result.scalars()}
        desired_names = {"group3", "group2", "group1"}

        to_insert = [GroupType(name=name) for name in desired_names if name not in existing_names]

        if to_insert:
            session.add_all(to_insert)
            await session.commit()
            print(f"Inserted group types: {[g.name for g in to_insert]}")
        else:
            print("Group types already seeded, nothing to insert.")


if __name__ == "__main__":
    asyncio.run(seed_group_types())
