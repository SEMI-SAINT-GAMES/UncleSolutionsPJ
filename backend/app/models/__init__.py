from bson import ObjectId
from pydantic import GetCoreSchemaHandler


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v, info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)
    @classmethod
    def __get_pydentic_json_schema__(cls, source, handler: GetCoreSchemaHandler):
        return handler(str)