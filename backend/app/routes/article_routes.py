from app.models import PaginationResponseModel
from app.models.article_models import ArticleCreate, ArticleOut
from bson import ObjectId
from core.db.mongo import get_mongodb
from core.pagination import Pagination
from core.utilies.auth.jwt_handlers import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException

article_router = APIRouter()

@article_router.get("/health")
async def health_check():
    return {"status": "ok"}
@article_router.get("/", response_model=PaginationResponseModel[ArticleOut])
async def read_articles(
    mongodb=Depends(get_mongodb),
    pagination: Pagination = Depends(),
    search: str | None = None,
    tags: str | None = None,
) -> dict[str, int | list]:
    pipeline = []

    if search:
        pipeline.append(
            {
                "$match": {
                    "$or": [
                        {"title": {"$regex": search, "$options": "i"}},
                        {"content": {"$regex": search, "$options": "i"}},
                    ]
                }
            }
        )

    if tags:
        pipeline.append({"$match": {"tags": {"$in": tags.split(",")}}})
    total = await mongodb["articles"].count_documents(
        pipeline[0]["$match"] if pipeline else {}
    )
    pipeline += [
        {
            "$lookup": {
                "from": "users",
                "localField": "author_id",
                "foreignField": "_id",
                "as": "author",
            }
        },
        {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}},
        {"$skip": pagination.skip},
        {"$limit": pagination.limit},
    ]
    cursor = await mongodb["articles"].aggregate(pipeline)
    articles = await cursor.to_list(length=None)
    response = pagination.create_pagination_response(
        total, [ArticleOut(**a) for a in articles]
    )
    return response


@article_router.post("/", response_model=ArticleOut)
async def create_article(
    article: ArticleCreate,
    user_id: str = Depends(get_current_user_id),
    mongodb=Depends(get_mongodb),
) -> ArticleOut:

    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = await mongodb["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    article.author_id = ObjectId(user_id)
    result = await mongodb["articles"].insert_one(article.dict())
    print(result.inserted_id)
    pipeline = [
        {"$match": {"_id": result.inserted_id}},
        {
            "$lookup": {
                "from": "users",
                "localField": "author_id",
                "foreignField": "_id",
                "as": "author",
            }
        },
        {"$unwind": "$author"},
    ]
    cursor = await mongodb["articles"].aggregate(pipeline)
    inserted_article = await cursor.to_list(1)
    print(inserted_article)
    return ArticleOut(**inserted_article[0])


@article_router.get("/{article_id}", response_model=ArticleOut)
async def read_article(article_id: str, mongodb=Depends(get_mongodb)) -> ArticleOut:
    pipeline = [
        {"$match": {"_id": ObjectId(article_id)}},
        {
            "$lookup": {
                "from": "users",
                "localField": "author_id",
                "foreignField": "_id",
                "as": "author",
            }
        },
        {"$unwind": "$author"},
    ]
    cursor = await mongodb["articles"].aggregate(pipeline)
    article = await cursor.to_list(1)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleOut(**article[0])


@article_router.get(
    "/by_user_id/{user_id}", response_model=PaginationResponseModel[ArticleOut]
)
async def read_articles_by_username(
    user_id: str, mongodb=Depends(get_mongodb), pagination: Pagination = Depends()
) -> dict[str, int | list]:
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "author_id",
                "foreignField": "_id",
                "as": "author",
            }
        },
        {"$unwind": "$author"},
        {"$match": {"author._id": ObjectId(user_id), "is_active": True}},
        {"$skip": pagination.skip},
        {"$limit": pagination.limit},
    ]
    total = await mongodb["articles"].count_documents(
        {"author_id": ObjectId(user_id), "is_active": True}
    )
    cursor = await mongodb["articles"].aggregate(pipeline)
    articles = await cursor.to_list(length=None)
    response = pagination.create_pagination_response(
        total, [ArticleOut(**a) for a in articles]
    )
    print(total)
    return response
