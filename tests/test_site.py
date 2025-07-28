from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.group import Group
from app.infrastructure.models.group_type import GroupType
from app.infrastructure.models.site import Site

pytestmark = pytest.mark.asyncio


@pytest.fixture
def french_date():
    return datetime(2025, 8, 2, 10, 0)  # Saturday


async def create_group_type(session: AsyncSession, name: str, can_associate: bool):
    group_type = GroupType(name=name, can_be_associated_with_site=can_associate)
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
    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
    json_response = response.json()
    assert "access_token" in json_response, f"Token not found: {json_response}"
    return json_response["access_token"]


async def test_create_french_site_valid(french_date, async_session, client):
    group_type = await create_group_type(async_session, "group1", True)
    group = await create_group(async_session, "G1", group_type.id)

    token = await get_token(client)
    payload = {
        "name": "Site FR",
        "country": "FR",
        "installation_date": french_date.isoformat(),
        "max_power_megawatt": 100.0,
        "min_power_megawatt": 10.0,
        "useful_energy_at_1_megawatt": 90.0,
        "group_ids": [group.id],
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Site FR"


async def test_create_french_site_same_day_should_fail(french_date, async_session, client):
    site = Site(
        name="Old Site",
        country="FR",
        installation_date=french_date,
        max_power_megawatt=90,
        min_power_megawatt=10,
        useful_energy_at_1_megawatt=85.0,
    )
    async_session.add(site)
    await async_session.commit()

    token = await get_token(client)
    payload = {
        "name": "Another Site FR",
        "country": "FR",
        "installation_date": french_date.isoformat(),
        "max_power_megawatt": 100.0,
        "min_power_megawatt": 10.0,
        "useful_energy_at_1_megawatt": 95.0,
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Only one French site" in response.text


async def test_create_italian_site_not_weekend_should_fail(async_session, client):
    weekday_date = datetime(2025, 8, 1, 10, 0)  # Friday

    token = await get_token(client)
    payload = {
        "name": "Site IT",
        "country": "IT",
        "installation_date": weekday_date.isoformat(),
        "max_power_megawatt": 100.0,
        "min_power_megawatt": 10.0,
        "efficiency": 0.87,
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Italian sites must be installed on weekends" in response.text


async def test_create_site_with_invalid_group_type(async_session, client):
    restricted_type = await create_group_type(async_session, "group3", False)
    restricted_group = await create_group(async_session, "Restricted G", restricted_type.id)

    token = await get_token(client)
    payload = {
        "name": "Invalid Association Site",
        "country": "FR",
        "installation_date": datetime(2025, 8, 3).isoformat(),
        "max_power_megawatt": 120.0,
        "min_power_megawatt": 20.0,
        "useful_energy_at_1_megawatt": 80.0,
        "group_ids": [restricted_group.id],
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "cannot be associated with a site" in response.text
