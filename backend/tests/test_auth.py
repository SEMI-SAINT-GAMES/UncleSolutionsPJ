import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport
from bson import ObjectId
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from core.db.mongo import get_mongodb


@pytest.mark.asyncio
async def test_register_user_success(monkeypatch, override_mongodb):
    async def fake_send_email(*args, **kwargs):
        return None

    def fake_hash_password(password: str) -> str:
        return "hashed-password"

    monkeypatch.setattr(
        "app.celery.tasks.send_welcome_email.delay",
        fake_send_email,
    )

    monkeypatch.setattr(
        "app.routes.auth_routes.hash_password",
        fake_hash_password,
    )

    payload = {
        "email": "test@test.com",
        "username": "testuser",
        "password": "StrongPassword123",
        "name": "Test",
        "surname": "User",
    }

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post("/auth/register", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert "password" not in data
    assert data["is_active"] is False
    assert "_id" in data

