import asyncio

from passlib.context import CryptContext
from sqlalchemy.future import select

from app.infrastructure.db import get_session
from app.infrastructure.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_user():
    async for session in get_session():
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("User already exists.")
            return

        user = User(username="admin", hashed_password=pwd_context.hash("password"))
        session.add(user)
        await session.commit()
        print("Admin user created.")


if __name__ == "__main__":
    asyncio.run(seed_user())
