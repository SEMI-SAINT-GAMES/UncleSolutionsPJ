import sys
import os
import pytest
from bson import ObjectId
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db.mongo import get_mongodb
from main import app


class FakeCursor:
    def __init__(self, data):
        self._data = data

    async def to_list(self, length=None):
        return self._data


class FakeCollection:
    def __init__(self):
        self._data = []

    async def insert_many(self, items):
        for item in items:
            item.setdefault("_id", ObjectId())
            self._data.append(item)

    async def delete_many(self, _):
        self._data.clear()

    async def count_documents(self, match):
        return len(self._apply_match(self._data, match))

    async def aggregate(self, pipeline):
        data = self._data

        for stage in pipeline:
            if "$match" in stage:
                data = self._apply_match(data, stage["$match"])

            if "$skip" in stage:
                data = data[stage["$skip"] :]

            if "$limit" in stage:
                data = data[: stage["$limit"]]

        return FakeCursor(data)

    def _apply_match(self, data, match):
        if not match:
            return data

        if "$or" in match:
            result = []
            for item in data:
                for condition in match["$or"]:
                    for field, rule in condition.items():
                        if "$regex" in rule:
                            if rule["$regex"].lower() in item.get(field, "").lower():
                                result.append(item)
                                break
            return result

        if "tags" in match and "$in" in match["tags"]:
            return [
                item for item in data
                if any(tag in item.get("tags", []) for tag in match["tags"]["$in"])
            ]

        return data


class FakeMongoDB(dict):
    def __init__(self):
        super().__init__()
        self["articles"] = FakeCollection()


@pytest.fixture
def override_mongodb():
    fake_db = FakeMongoDB()

    async def _override():
        return fake_db

    app.dependency_overrides[get_mongodb] = _override
    yield fake_db
    app.dependency_overrides.clear()


@pytest.fixture
async def articles_in_db(override_mongodb):
    db = override_mongodb

    articles = [
        {
            "_id": ObjectId(),
            "title": "FastAPI testing",
            "content": "How to test FastAPI with MongoDB",
            "tags": ["python", "fastapi"],
            "author_id": None,
        },
        {
            "_id": ObjectId(),
            "title": "Django testing",
            "content": "Testing Django applications",
            "tags": ["python", "django"],
            "author_id": None,
        },
        {
            "_id": ObjectId(),
            "title": "MongoDB tips",
            "content": "Indexes and aggregation",
            "tags": ["mongodb"],
            "author_id": None,
        },
    ]

    await db["articles"].insert_many(articles)
    yield
    await db["articles"].delete_many({})



