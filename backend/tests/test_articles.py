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


@pytest.mark.asyncio
async def test_read_articles_with_filters(

    articles_in_db,
):
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/articles/",
            params={
                "search": "testing",
                "tags": "python",
                "limit": 10,
                "page": 1,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total_count" in data
    assert isinstance(data["items"], list)

    assert data["total_count"] == 3
    assert len(data["items"]) == 3

    titles = {item["title"] for item in data["items"]}

    assert "FastAPI testing" in titles
    assert "Django testing" in titles
    assert "MongoDB tips" not in titles
