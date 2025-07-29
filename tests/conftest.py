import asyncio

import pytest_asyncio
from httpx import AsyncClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.db import Base, get_session
from app.infrastructure.models.user import User
from app.main import app

DATABASE_TEST_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(DATABASE_TEST_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine_test, expire_on_commit=False)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest_asyncio.fixture(autouse=True)
async def create_test_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        hashed_pw = pwd_context.hash("password")
        session.add(User(username="admin", hashed_password=hashed_pw))
        await session.commit()

    yield


@pytest_asyncio.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest_asyncio.fixture()
async def async_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def client(async_session: AsyncSession):
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
