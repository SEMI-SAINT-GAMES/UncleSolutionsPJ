import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import backend.core.db.mongo as mongo_module


@pytest.mark.asyncio
async def test_connect_to_mongo():
    fake_client = MagicMock()
    fake_db = MagicMock()
    fake_client.__getitem__.return_value = fake_db

    with patch.object(mongo_module, "AsyncMongoClient", return_value=fake_client):
        with patch("os.getenv") as getenv_mock:
            getenv_mock.side_effect = lambda key: {
                "MONGO_URL": "mongodb://localhost:27017",
                "MONGO_DB_NAME": "testdb",
            }[key]

            mongo_module.mongodb_client = None
            mongo_module.mongodb = None

            db = await mongo_module.connect_to_mongo()

            assert db is fake_db
            assert mongo_module.mongodb is fake_db
            assert mongo_module.mongodb_client is fake_client


@pytest.mark.asyncio
async def test_get_mongodb():
    fake_db = MagicMock()

    with patch.object(
        mongo_module,
        "connect_to_mongo",
        AsyncMock(return_value=fake_db),
    ):
        mongo_module.mongodb = None
        mongo_module.mongodb_client = None

        db = await mongo_module.get_mongodb()

        assert db is fake_db


@pytest.mark.asyncio
async def test_close_mongo():
    fake_client = AsyncMock()

    mongo_module.mongodb_client = fake_client

    await mongo_module.close_mongo()

    fake_client.close.assert_awaited_once()
