import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.group import Group
from app.infrastructure.models.group_type import GroupType

pytestmark = pytest.mark.asyncio


async def create_group_type(session: AsyncSession, name: str):
    group_type = GroupType(name=name, can_be_associated_with_site=True)
    session.add(group_type)
    await session.commit()
    await session.refresh(group_type)
    return group_type


async def create_group(session: AsyncSession, name: str, group_type_id: int):
    group = Group(name=name, type_id=group_type_id)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


async def get_token(client: AsyncClient):
    response = await client.post("/auth/login", data={"username": "admin", "password": "password"})
    return response.json()["access_token"]


async def test_create_group(async_session, client):
    group_type = await create_group_type(async_session, "Energy")
    token = await get_token(client)

    payload = {"name": "Group A", "type_id": group_type.id}
    response = await client.post(
        "/groups/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Group A"


async def test_list_groups(async_session, client):
    group_type = await create_group_type(async_session, "Energy")
    await create_group(async_session, "Group B", group_type.id)
    token = await get_token(client)

    response = await client.get("/groups/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert any(group["name"] == "Group B" for group in response.json())


async def test_filter_and_sort_groups(async_session, client):
    group_type = await create_group_type(async_session, "Energy")
    await create_group(async_session, "Alpha", group_type.id)
    await create_group(async_session, "Beta", group_type.id)
    token = await get_token(client)

    response = await client.get("/groups/?name=Al", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert all("Al" in group["name"] for group in response.json())

    response = await client.get(
        "/groups/?sort_by=name&desc=true", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert sorted([g["name"] for g in response.json()], reverse=True) == [
        g["name"] for g in response.json()
    ]


async def test_update_group(async_session, client):
    group_type = await create_group_type(async_session, "Energy")
    group = await create_group(async_session, "Old Name", group_type.id)
    token = await get_token(client)

    payload = {"name": "New Name", "type_id": group_type.id}
    response = await client.put(
        f"/groups/{group.id}", json=payload, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["type_id"] == group_type.id


async def test_update_nonexistent_group(async_session, client):
    group_type = await create_group_type(async_session, "AnyType")
    token = await get_token(client)

    payload = {"name": "Doesn't Matter", "type_id": group_type.id}
    response = await client.put(
        "/groups/9999", json=payload, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert "Group not found" in response.text


async def test_delete_group(async_session, client):
    group_type = await create_group_type(async_session, "Energy")
    group = await create_group(async_session, "ToDelete", group_type.id)
    token = await get_token(client)

    response = await client.delete(
        f"/groups/{group.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

    # Check if really deleted
    response = await client.get("/groups/", headers={"Authorization": f"Bearer {token}"})
    assert all(g["id"] != group.id for g in response.json())


async def test_delete_nonexistent_group(client):
    token = await get_token(client)
    response = await client.delete("/groups/9999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Group not found"
