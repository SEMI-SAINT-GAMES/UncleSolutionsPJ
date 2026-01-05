import sys
import os
import pytest
from bson import ObjectId


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.utilies.auth.jwt_handlers import get_current_user_id
from core.db.mongo import get_mongodb
from main import app


class FakeCursor:
    def __init__(self, data):
        self._data = data

    async def to_list(self, length=None):
        if length is None:
            return self._data
        return self._data[:length]


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCollection:
    def __init__(self):
        self._data = []
        self._db = None  # back-reference для $lookup

    async def insert_many(self, items):
        for item in items:
            item.setdefault("_id", ObjectId())
            self._data.append(item)

    async def insert_one(self, item):
        item["_id"] = ObjectId()
        self._data.append(item)
        return FakeInsertResult(item["_id"])

    async def delete_many(self, _):
        self._data.clear()

    async def find_one(self, query):
        for item in self._data:
            if all(item.get(k) == v for k, v in query.items()):
                return item
        return None

    async def count_documents(self, match):
        return len(self._apply_match(self._data, match))

    async def aggregate(self, pipeline):
        data = self._data

        for stage in pipeline:
            if "$match" in stage:
                data = self._apply_match(data, stage["$match"])

            if "$lookup" in stage:
                from_collection = stage["$lookup"]["from"]
                local_field = stage["$lookup"]["localField"]
                foreign_field = stage["$lookup"]["foreignField"]
                as_field = stage["$lookup"]["as"]

                foreign_data = self._db[from_collection]._data
                for item in data:
                    item[as_field] = [
                        f for f in foreign_data
                        if f.get(foreign_field) == item.get(local_field)
                    ]

            if "$unwind" in stage:
                path = stage["$unwind"]
                if isinstance(path, dict):
                    path = path["path"]
                key = path.lstrip("$")
                for item in data:
                    if isinstance(item.get(key), list):
                        item[key] = item[key][0] if item[key] else None

            if "$skip" in stage:
                data = data[stage["$skip"] :]

            if "$limit" in stage:
                data = data[: stage["$limit"]]

        return FakeCursor(data)

    def _get_nested_value(self, item: dict, path: str):
        value = item
        for part in path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value

    def _match_condition(self, item, condition: dict) -> bool:
        for field, rule in condition.items():
            value = self._get_nested_value(item, field)

            if isinstance(rule, dict):
                if "$regex" in rule:
                    if value is None:
                        return False
                    if rule["$regex"].lower() not in str(value).lower():
                        return False

                elif "$in" in rule:
                    if not isinstance(value, list):
                        return False
                    if not any(v in value for v in rule["$in"]):
                        return False

                else:
                    return False

            else:
                if value != rule:
                    return False

        return True

    def _apply_match(self, data, match):
        if not match:
            return data

        result = []

        for item in data:
            ok = True

            for key, value in match.items():
                if key == "$or":
                    if not any(self._match_condition(item, cond) for cond in value):
                        ok = False
                        break
                else:
                    if not self._match_condition(item, {key: value}):
                        ok = False
                        break

            if ok:
                result.append(item)

        return result


class FakeMongoDB(dict):
    def __init__(self):
        super().__init__()
        self["articles"] = FakeCollection()
        self["users"] = FakeCollection()

        # back-references для $lookup
        self["articles"]._db = self
        self["users"]._db = self


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

    await override_mongodb["articles"].insert_many(articles)
    yield
    await override_mongodb["articles"].delete_many({})


@pytest.fixture
async def user_in_db(override_mongodb):
    user_id = ObjectId()
    override_mongodb["users"]._data.append(
        {
            "_id": user_id,
            "email": "test@test.com",
            "name": "Test",
            "surname": "User",
            "username": "testuser",
        }
    )
    return str(user_id)


@pytest.fixture
def override_current_user(user_in_db):
    async def _override():
        return user_in_db

    app.dependency_overrides[get_current_user_id] = _override
    yield
    app.dependency_overrides.pop(get_current_user_id, None)
