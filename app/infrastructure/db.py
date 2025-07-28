from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.config import get_settings

Base = declarative_base()

engine = create_async_engine(str(get_settings().db_url), echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that provides a database session.
    Designed to be used with FastAPI's Depends, but also usable in CLI scripts.
    """
    async with async_session_maker() as session:
        yield session
