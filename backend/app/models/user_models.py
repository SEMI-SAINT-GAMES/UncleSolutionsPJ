from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId



class User(BaseModel):
    name: str
    surname: str
    username: str
    email: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RegisterUser(User):
    password: str

class LoginUser(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

