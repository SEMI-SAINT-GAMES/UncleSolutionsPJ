from typing import List, Optional

from app.models import CreateModel, PyObjectId
from app.models.user_models import User, UserOut
from bson import ObjectId
from pydantic import BaseModel, Field


class ArticleBase(BaseModel):
    title: str
    content: str
    tags: Optional[list[str]] = []


class Article(ArticleBase):
    id: Optional[PyObjectId] = Field(alias="_id")
    is_active: bool = True

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ArticleCreate(ArticleBase, CreateModel):
    author_id: Optional[PyObjectId] = None


class ArticleOut(Article):
    author: UserOut | None = None


class PageInfo(BaseModel):
    total_count: int
    total_pages: int
    current_page: int
    limit: int


class ArticleInProfileModel(BaseModel):
    paginated: List[Article]
    page_info: PageInfo


class ProfileModel(User):
    articles: ArticleInProfileModel
