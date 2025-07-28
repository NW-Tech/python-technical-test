import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.group_type import GroupType
from tests.test_group import get_token

pytestmark = pytest.mark.asyncio


async def create_group_type(session: AsyncSession, name: str):
    group_type = GroupType(name=name)
    session.add(group_type)
    await session.commit()
    await session.refresh(group_type)
    return group_type


async def test_create_group_type(async_session, client):
    token = await get_token(client)
    payload = {"name": "Type A"}
    response = await client.post(
        "/group_types/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Type A"


async def test_create_group_type_duplicate_should_fail(async_session, client):
    await create_group_type(async_session, "Duplicated")
    token = await get_token(client)
    payload = {"name": "Duplicated"}
    response = await client.post(
        "/group_types/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "already exists" in response.text


async def test_list_group_types_with_filter_and_sort(async_session, client):
    await create_group_type(async_session, "B-Type")
    await create_group_type(async_session, "A-Type")
    token = await get_token(client)

    response = await client.get(
        "/group_types/?sort_by=name&desc=false", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    names = [gt["name"] for gt in response.json()]
    assert names == sorted(names)

    response_filtered = await client.get(
        "/group_types/?name=B", headers={"Authorization": f"Bearer {token}"}
    )
    assert response_filtered.status_code == 200
    assert any("B-Type" in gt["name"] for gt in response_filtered.json())


async def test_update_group_type(async_session, client):
    group_type = await create_group_type(async_session, "OldName")
    token = await get_token(client)
    payload = {"name": "UpdatedName"}

    response = await client.put(
        f"/group_types/{group_type.id}", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "UpdatedName"


async def test_update_nonexistent_group_type(client):
    token = await get_token(client)
    response = await client.put(
        "/group_types/9999",
        json={"name": "DoesNotExist"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "not found" in response.text


async def test_delete_group_type(async_session, client):
    group_type = await create_group_type(async_session, "ToDelete")
    token = await get_token(client)
    response = await client.delete(
        f"/group_types/{group_type.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

    check = await async_session.get(GroupType, group_type.id)
    assert check is None


async def test_delete_nonexistent_group_type(client):
    token = await get_token(client)
    response = await client.delete(
        "/group_types/9999", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    assert "not found" in response.text
