import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_response_model(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert "status" in data
    assert isinstance(data["status"], str)
