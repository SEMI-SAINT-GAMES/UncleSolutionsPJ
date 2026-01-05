import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db.mongo import get_mongodb
from main import app
class FakeCursor:
    async def to_list(self, length=None):
        return []


class FakeCollection:
    async def count_documents(self, *args, **kwargs):
        return 0

    async def aggregate(self, pipeline):
        return FakeCursor()


class FakeMongoDB(dict):
    def __getitem__(self, item):
        return FakeCollection()

@pytest.fixture
def override_mongodb():
    async def _override():
        return FakeMongoDB()

    app.dependency_overrides[get_mongodb] = _override
    yield
    app.dependency_overrides.clear()