from datetime import datetime, timedelta
from typing import Optional, TypeVar, Generic, List
from pydantic.generics import GenericModel
from bson import ObjectId
from pydantic import GetCoreSchemaHandler, BaseModel, Field

class CreateModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = True

class UpdateModel(BaseModel):
    updated_at: datetime = Field(default_factory=datetime.utcnow)
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


T = TypeVar("T")
class PaginationResponseModel(GenericModel, Generic[T]):
    total_count: int
    total_pages: int
    current_page: int
    limit: int
    items: List[T]

class VerifyRequest(BaseModel):
    code: str
    username: str

class ForgotPasswordRequest(BaseModel):
    email: str

class UsernameRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    verify: VerifyRequest
    new_password: str
class VerifyModel(BaseModel):
    hashcode: str
    username: str
    expire_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
