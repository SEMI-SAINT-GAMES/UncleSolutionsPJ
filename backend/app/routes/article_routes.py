from fastapi import APIRouter, HTTPException, Depends

from app.models.article_models import ArticleCreate, ArticleBase, Article
from core.db.mongo import get_mongodb
from core.utilies.auth.jwt_handlers import get_current_username

article_router = APIRouter()

@article_router.get("/", response_model=list[Article])
async def read_articles(mongodb=Depends(get_mongodb)):
    articles = await mongodb["articles"].find().to_list(None)
    return articles

@article_router.post("/", response_model=Article)
async def create_article(article: ArticleCreate, username: str = Depends(get_current_username), mongodb = Depends(get_mongodb)):
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = await mongodb["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    article.author_id = user["_id"]
    result = await mongodb["articles"].insert_one(article.dict())
    inserted_article = await mongodb["articles"].find_one({"_id": result.inserted_id})
    return inserted_article

@article_router.get("/{article_id}", response_model=Article)
async def read_article(article_id: str, mongodb = Depends(get_mongodb)):
    article = await mongodb["articles"].find_one({"_id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@article_router.get("/by_username/{username}", response_model=list[Article])
async def read_articles_by_username(username: str, mongodb=Depends(get_mongodb)):
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = await mongodb["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user["_id"]
    print(">>>>>", user_id)
    articles = await mongodb["articles"].find({"author_id": user_id}).to_list(None)
    return articles