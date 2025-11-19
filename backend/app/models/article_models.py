from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from app.models import PyObjectId, CreateModel


class ArticleBase(BaseModel):
    title: str
    content: str
    tags: Optional[list[str]] = []
    author_id: Optional[PyObjectId] = None



class Article(ArticleBase):
    id: Optional[PyObjectId] = Field(alias="_id")
    is_active: bool = True
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ArticleCreate(ArticleBase, CreateModel):
    pass

