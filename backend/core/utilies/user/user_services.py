from core.db.mongo import get_mongodb
from fastapi import Depends


async def find_user_by_username(username, mongodb=Depends(get_mongodb)):
    return await mongodb["users"].find_one({"username": username})


async def find_user_by_email(email, mongodb=Depends(get_mongodb)):
    return await mongodb["users"].find_one({"email": email})


async def find_user_by_id(user_id, mongodb=Depends(get_mongodb)):
    return await mongodb["users"].find_one({"_id": user_id})
