import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user import User
from app.utils.auth import get_hashed_password

pytestmark = pytest.mark.asyncio


async def test_login_success(async_session: AsyncSession, client: AsyncClient):
    user = User(username="authuser", hashed_password=get_hashed_password("correctpass"))
    async_session.add(user)
    await async_session.commit()

    response = await client.post(
        "/auth/login",
        data={"username": "authuser", "password": "correctpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


async def test_login_wrong_password(async_session: AsyncSession, client: AsyncClient):
    user = User(username="authuser2", hashed_password=get_hashed_password("secret"))
    async_session.add(user)
    await async_session.commit()

    response = await client.post(
        "/auth/login",
        data={"username": "authuser2", "password": "wrongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        data={"username": "ghost", "password": "ghostpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
