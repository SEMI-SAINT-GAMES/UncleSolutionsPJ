from typing import List, Optional
from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from enum import Enum
from bson import ObjectId

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

class User(BaseModel):
    name: str
    surname: str
    username: str
    email: str
    password: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class LoginUser(BaseModel):
    username: str
    password: str

