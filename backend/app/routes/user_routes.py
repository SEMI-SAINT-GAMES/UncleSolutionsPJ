from typing import List

from fastapi import APIRouter, HTTPException, Depends
from app.models.user_models import UpdateUserDTO, User
from core.db.mongo import get_mongodb
from core.utilies.auth.jwt_handlers import get_current_username

user_router = APIRouter()

@user_router.get("/profile", response_model=User)
async def profile(username: str = Depends(get_current_username), mongodb = Depends(get_mongodb)):
    user = mongodb["users"].find_one({"username": username})
    if not user:
        raise HTTPException(404, "User not found")
    return user

@user_router.get("/", response_model=List[User])
async def read_users(mongodb = Depends(get_mongodb)):
    users = await mongodb["users"].find().to_list(None)
    return users


@user_router.get("/{email}", response_model=User)
async def read_user_by_email(email: str, mongodb = Depends(get_mongodb)):
    user = await mongodb["users"].find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
@user_router.put("/update/{email}", response_model=User)
async def update_user(email: str, dto: UpdateUserDTO, mongodb = Depends(get_mongodb)):
    await mongodb["users"].update_one(
        {"email": email},
        {"$set": dto.dict(exclude_unset=True)}
    )
    return await mongodb["users"].find_one({"email": email})

