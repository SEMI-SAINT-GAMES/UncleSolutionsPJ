from fastapi import APIRouter, HTTPException
from app import db
from app.models import User, PyObjectId
from bson import ObjectId
from typing import Optional
user_router = APIRouter()
@user_router.get("/user", response_model=list[User])
async def get_users():
    users = db["users"].find()
    return [User(**user) for user in users]

@user_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: PyObjectId):
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if user:
        return User(**user)
    raise HTTPException(status_code=404, detail="User not found")

@user_router.post("/users", response_model=User)
async def create_user(user: User):
    try:
        user_dict = user.dict(by_alias=True)
        result = await db["user"].insert_one(user_dict)
        inserted_user = await db["users"].find_one({"_id": result.inserted_id})
        return User(**inserted_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user{str(e)}")
