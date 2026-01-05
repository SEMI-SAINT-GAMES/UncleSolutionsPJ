import sys
import os
import pytest
from bson import ObjectId
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


@pytest.mark.asyncio
async def test_create_article_success(
    override_mongodb,
    override_current_user,
):

    transport = ASGITransport(app=app)

    payload = {
        "title": "My first article",
        "content": "Hello from test",
        "tags": ["python", "fastapi"],
    }

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post("/articles/", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == payload["title"]
    assert data["content"] == payload["content"]
    assert data["tags"] == payload["tags"]

    assert "_id" in data
    assert isinstance(data["_id"], str)

    assert "author" in data
    assert data["author"]["email"] == "test@test.com"


@pytest.mark.asyncio
async def test_read_article_by_id_success(override_mongodb):
    user_id = ObjectId()
    article_id = ObjectId()

    override_mongodb["users"]._data.append(
        {
            "_id": user_id,
            "name": "Test",
            "surname": "User",
            "username": "testuser",
            "email": "test@test.com",
        }
    )

    override_mongodb["articles"]._data.append(
        {
            "_id": article_id,
            "title": "Test article",
            "content": "Article content",
            "tags": ["python"],
            "author_id": user_id,
        }
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(f"/articles/{article_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["_id"] == str(article_id)
    assert data["title"] == "Test article"
    assert data["author"]["email"] == "test@test.com"
    assert data["author"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_read_article_by_id_not_found(override_mongodb):
    article_id = ObjectId()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(f"/articles/{article_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"


