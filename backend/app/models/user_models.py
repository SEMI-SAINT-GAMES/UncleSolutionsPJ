from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

from app.models import PyObjectId, CreateModel, UpdateModel


class UserBase(BaseModel):
    name: str
    surname: str
    username: str
    email: str


class User(UserBase):
    id: Optional[PyObjectId] = Field(alias="_id")
    is_active: bool = False
    is_author: bool = False

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class RegisterUser(UserBase, CreateModel):
    password: str
    is_author: bool = False


class LoginUser(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str
    last_login: datetime = Field(default_factory=datetime.utcnow)


class UpdateUserDTO(UserBase, UpdateModel):
    pass


class UserOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    surname: str
    username: str
    email: str

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
