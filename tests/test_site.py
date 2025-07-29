from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.group import Group
from app.infrastructure.models.group_type import GroupType
from app.infrastructure.models.site import Site

pytestmark = pytest.mark.asyncio


@pytest.fixture
def weekend_date():
    """Returns a Saturday for IT/FR."""
    return datetime(2025, 8, 2, 10, 0)


@pytest.fixture
def weekday_date():
    """Returns a Friday for IT/FR."""
    return datetime(2025, 8, 1, 10, 0)


async def create_group_type(session: AsyncSession, name: str, can_associate: bool):
    gt = GroupType(name=name, can_be_associated_with_site=can_associate)
    session.add(gt)
    await session.commit()
    await session.refresh(gt)
    return gt


async def create_group(session: AsyncSession, name: str, group_type_id: int):
    g = Group(name=name, type_id=group_type_id)
    session.add(g)
    await session.commit()
    await session.refresh(g)
    return g


async def get_token(client: AsyncClient):
    response = await client.post("/auth/login", data={"username": "admin", "password": "password"})
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_create_french_site_success(weekend_date, async_session, client):
    group_type = await create_group_type(async_session, "group1", True)
    group = await create_group(async_session, "G1", group_type.id)
    token = await get_token(client)
    payload = {
        "name": "French Site",
        "country": "FR",
        "installation_date": weekend_date.isoformat(),
        "max_power_megawatt": 40.0,
        "min_power_megawatt": 10.0,
        "useful_energy_at_1_megawatt": 30.0,
        "group_ids": [group.id],
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["country"] == "FR"
    assert group.id in data["group_ids"]


async def test_create_italian_site_success(weekend_date, async_session, client):
    group_type = await create_group_type(async_session, "group2", True)
    group = await create_group(async_session, "G2", group_type.id)
    token = await get_token(client)
    payload = {
        "name": "Italian Site",
        "country": "IT",
        "installation_date": weekend_date.isoformat(),
        "max_power_megawatt": 100.0,
        "min_power_megawatt": 50.0,
        "efficiency": 0.99,
        "group_ids": [group.id],
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["country"] == "IT"
    assert data["efficiency"] == 0.99
    assert group.id in data["group_ids"]


async def test_create_site_invalid_country(client):
    token = await get_token(client)
    payload = {
        "name": "Invalid Country",
        "country": "ES",
        "installation_date": "2025-08-02T10:00:00",
        "max_power_megawatt": 80.0,
        "min_power_megawatt": 20.0,
        "useful_energy_at_1_megawatt": 15.0,
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


async def test_create_fr_missing_required_field(weekend_date, client):
    token = await get_token(client)
    payload = {
        "name": "FR missing field",
        "country": "FR",
        "installation_date": weekend_date.isoformat(),
        "max_power_megawatt": 40.0,
        "min_power_megawatt": 10.0,
        # Missing 'useful_energy_at_1_megawatt'
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    assert "useful_energy_at_1_megawatt" in response.text


async def test_create_it_missing_required_field(weekend_date, client):
    token = await get_token(client)
    payload = {
        "name": "IT missing field",
        "country": "IT",
        "installation_date": weekend_date.isoformat(),
        "max_power_megawatt": 100.0,
        "min_power_megawatt": 50.0,
        # Missing 'efficiency'
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    assert "efficiency" in response.text


async def test_create_french_site_same_day_should_fail(weekend_date, async_session, client):
    site = Site(
        name="Old Site",
        country="FR",
        installation_date=weekend_date,
        max_power_megawatt=10,
        min_power_megawatt=5,
        useful_energy_at_1_megawatt=5,
    )
    async_session.add(site)
    await async_session.commit()

    token = await get_token(client)
    payload = {
        "name": "Another FR",
        "country": "FR",
        "installation_date": weekend_date.isoformat(),
        "max_power_megawatt": 50.0,
        "min_power_megawatt": 20.0,
        "useful_energy_at_1_megawatt": 25.0,
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Only one French site" in response.text


async def test_create_italian_site_not_weekend_should_fail(weekday_date, client):
    token = await get_token(client)
    payload = {
        "name": "Site IT Not Weekend",
        "country": "IT",
        "installation_date": weekday_date.isoformat(),
        "max_power_megawatt": 30.0,
        "min_power_megawatt": 10.0,
        "efficiency": 0.7,
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Italian sites must be installed on weekends" in response.text


async def test_create_with_restricted_group(weekend_date, async_session, client):
    restricted_type = await create_group_type(async_session, "restricted", False)
    restricted_group = await create_group(async_session, "Restricted G", restricted_type.id)
    token = await get_token(client)
    payload = {
        "name": "Invalid Association",
        "country": "FR",
        "installation_date": weekend_date.isoformat(),
        "max_power_megawatt": 20.0,
        "min_power_megawatt": 5.0,
        "useful_energy_at_1_megawatt": 5.0,
        "group_ids": [restricted_group.id],
    }
    response = await client.post(
        "/sites/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "cannot be associated with a site" in response.text


async def test_list_sites(client, async_session, weekend_date):
    site1 = Site(
        name="Site 1",
        country="FR",
        installation_date=weekend_date,
        max_power_megawatt=10,
        min_power_megawatt=2,
        useful_energy_at_1_megawatt=7,
    )
    async_session.add(site1)
    site2 = Site(
        name="Site 2",
        country="IT",
        installation_date=weekend_date,
        max_power_megawatt=50,
        min_power_megawatt=20,
        efficiency=0.8,
    )
    async_session.add(site2)
    await async_session.commit()
    token = await get_token(client)
    response = await client.get("/sites/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert any(s["name"] == "Site 1" for s in result)
    assert any(s["name"] == "Site 2" for s in result)


async def test_list_sites_with_name_filter(client, async_session, weekend_date):
    site = Site(
        name="FilterMe",
        country="FR",
        installation_date=weekend_date,
        max_power_megawatt=30,
        min_power_megawatt=5,
        useful_energy_at_1_megawatt=10,
    )
    async_session.add(site)
    await async_session.commit()
    token = await get_token(client)
    response = await client.get(
        "/sites/?name=filterme", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert any("FilterMe" in s["name"] for s in result)


async def test_update_site_success(weekend_date, async_session, client):
    site = Site(
        name="ToUpdate",
        country="FR",
        installation_date=weekend_date,
        max_power_megawatt=10,
        min_power_megawatt=2,
        useful_energy_at_1_megawatt=8,
    )
    async_session.add(site)
    await async_session.commit()
    token = await get_token(client)
    payload = {"name": "UpdatedName", "max_power_megawatt": 99.0, "useful_energy_at_1_megawatt": 8}
    response = await client.put(
        f"/sites/{site.id}", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "UpdatedName"
    assert data["max_power_megawatt"] == 99.0


async def test_update_site_fail_rules(weekend_date, async_session, client):
    site = Site(
        name="Update FR",
        country="FR",
        installation_date=weekend_date,
        max_power_megawatt=10,
        min_power_megawatt=2,
        useful_energy_at_1_megawatt=8,
    )
    async_session.add(site)
    await async_session.commit()
    site2 = Site(
        name="Other FR",
        country="FR",
        installation_date=weekend_date,
        max_power_megawatt=12,
        min_power_megawatt=4,
        useful_energy_at_1_megawatt=7,
    )
    async_session.add(site2)
    await async_session.commit()
    token = await get_token(client)
    payload = {
        "country": "FR",
        "installation_date": weekend_date.isoformat(),
        "useful_energy_at_1_megawatt": 7,
    }
    response = await client.put(
        f"/sites/{site2.id}", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Only one French site" in response.text


async def test_update_site_not_found(client):
    token = await get_token(client)
    payload = {"name": "Doesn't matter", "useful_energy_at_1_megawatt": 1}
    response = await client.put(
        "/sites/99999", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


async def test_delete_site_success(weekend_date, async_session, client):
    site = Site(
        name="ToDelete",
        country="FR",
        installation_date=weekend_date,
        max_power_megawatt=10,
        min_power_megawatt=2,
        useful_energy_at_1_megawatt=6,
    )
    async_session.add(site)
    await async_session.commit()
    token = await get_token(client)
    response = await client.delete(
        f"/sites/{site.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    response = await client.put(
        f"/sites/{site.id}",
        json={"name": "fail", "useful_energy_at_1_megawatt": 6},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


async def test_delete_site_not_found(client):
    token = await get_token(client)
    response = await client.delete("/sites/99999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
