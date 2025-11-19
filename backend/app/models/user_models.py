from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

from app.models import PyObjectId

class UserBase(BaseModel):
    name: str
    surname: str
    username: str
    email: str

class User(UserBase):
    id: Optional[PyObjectId] = Field(alias="_id")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RegisterUser(UserBase):
    password: str

class LoginUser(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

class UpdateUserDTO(BaseModel):
    other_names: List[str] = None
    age: int = None

