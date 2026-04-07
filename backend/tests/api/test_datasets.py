import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_dataset(client: AsyncClient):
    response = await client.post(
        "/api/datasets",
        json={"name": "Test Dataset", "description": "A test dataset"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Dataset"
    assert data["description"] == "A test dataset"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_dataset_duplicate_name(client: AsyncClient):
    await client.post("/api/datasets", json={"name": "Duplicate"})
    response = await client.post("/api/datasets", json={"name": "Duplicate"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_datasets_empty(client: AsyncClient):
    response = await client.get("/api/datasets")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_datasets(client: AsyncClient):
    await client.post("/api/datasets", json={"name": "DS1"})
    await client.post("/api/datasets", json={"name": "DS2"})
    response = await client.get("/api/datasets")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_bulk_upload_cases(client: AsyncClient):
    ds = await client.post("/api/datasets", json={"name": "For Cases"})
    dataset_id = ds.json()["id"]

    response = await client.post(
        f"/api/datasets/{dataset_id}/cases",
        json={
            "cases": [
                {"input": "Q1", "reference_output": "A1"},
                {"input": "Q2", "reference_output": "A2", "metadata": {"tag": "hard"}},
            ]
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["input"] == "Q1"
    assert data[1]["metadata"] == {"tag": "hard"}


@pytest.mark.asyncio
async def test_bulk_upload_cases_dataset_not_found(client: AsyncClient):
    response = await client.post(
        "/api/datasets/9999/cases",
        json={"cases": [{"input": "Q", "reference_output": "A"}]},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_cases(client: AsyncClient):
    ds = await client.post("/api/datasets", json={"name": "For List Cases"})
    dataset_id = ds.json()["id"]
    await client.post(
        f"/api/datasets/{dataset_id}/cases",
        json={"cases": [{"input": "Q1", "reference_output": "A1"}]},
    )
    response = await client.get(f"/api/datasets/{dataset_id}/cases")
    assert response.status_code == 200
    assert len(response.json()) == 1
