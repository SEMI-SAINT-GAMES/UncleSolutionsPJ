from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.models.article_models import ProfileModel
from app.models.user_models import UpdateUserDTO, User
from core.db.mongo import get_mongodb
from core.utilies.auth.jwt_handlers import get_current_user_id

user_router = APIRouter()

@user_router.get("/profile", response_model=ProfileModel)
async def profile(user_id: str = Depends(get_current_user_id), mongodb = Depends(get_mongodb)):
    print(user_id)
    if not user_id:
        raise HTTPException(401, "Unauthorized")
    pipeline = [
        {"$match": {"_id": ObjectId(user_id)}},
        {
            "$lookup":{
                "from": "articles",
                "localField": "_id",
                "foreignField": "author_id",
                "as": "articles"
            }
        }
    ]
    user = await mongodb["users"].aggregate(pipeline).to_list(length=1)
    if not user:
        raise HTTPException(404, "User not found")
    return ProfileModel(**user[0])

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

