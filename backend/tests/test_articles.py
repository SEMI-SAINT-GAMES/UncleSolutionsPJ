import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

@pytest.mark.asyncio
async def test_read_articles_simple(override_mongodb):
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/articles/")

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["items"] == []

    assert "total_count" in data
    assert data["total_count"] == 0



