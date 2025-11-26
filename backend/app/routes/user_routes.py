from app.models import PaginationResponseModel
from app.models.article_models import ProfileModel
from app.models.user_models import UpdateUserDTO, User
from bson import ObjectId
from core.db.mongo import get_mongodb
from core.pagination import Pagination
from core.utilies.auth.jwt_handlers import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException

user_router = APIRouter()


@user_router.get("/profile", response_model=ProfileModel)
async def profile(
    user_id: str = Depends(get_current_user_id),
    mongodb=Depends(get_mongodb),
    pagination: Pagination = Depends(),
):
    if not user_id:
        raise HTTPException(401, "Unauthorized")

    pipeline = [
        {"$match": {"_id": ObjectId(user_id)}},
        {
            "$lookup": {
                "from": "articles",
                "let": {"user_id": "$_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {"$eq": ["$author_id", "$$user_id"]},
                            "is_active": True,
                        }
                    },
                    {"$sort": {"created_at": -1}},
                    {
                        "$facet": {
                            "paginated": [
                                {"$skip": pagination.skip},
                                {"$limit": pagination.limit},
                            ],
                            "page_info": [{"$count": "total_count"}],
                        }
                    },
                ],
                "as": "articles",
            }
        },
    ]

    cursor = await mongodb["users"].aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise HTTPException(404, "User not found")
    user_data = result[0]
    total_count = (
        user_data["articles"][0]["page_info"][0]["total_count"]
        if user_data["articles"][0]["page_info"]
        else 0
    )
    page_info = pagination.create_user_profile_pagination_response(total_count)
    user_data["articles"] = {
        "page_info": page_info,
        "paginated": user_data["articles"][0]["paginated"],
    }
    return ProfileModel(**user_data)


@user_router.get("/", response_model=PaginationResponseModel[User])
async def read_users(mongodb=Depends(get_mongodb), pagination: Pagination = Depends()):
    total = await mongodb["users"].count_documents({"is_active": True})
    cursor = (
        mongodb["users"]
        .find({"is_active": True})
        .skip(pagination.skip)
        .limit(pagination.limit)
    )
    users = await cursor.to_list(length=pagination.limit)
    response = pagination.create_pagination_response(total, users)
    return response


@user_router.get("/{email}", response_model=User)
async def read_user_by_email(email: str, mongodb=Depends(get_mongodb)):
    user = await mongodb["users"].find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@user_router.put("/update/{email}", response_model=User)
async def update_user(email: str, dto: UpdateUserDTO, mongodb=Depends(get_mongodb)):
    await mongodb["users"].update_one(
        {"email": email}, {"$set": dto.dict(exclude_unset=True)}
    )
    return await mongodb["users"].find_one({"email": email})
