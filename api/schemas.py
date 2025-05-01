from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# --- Profile Schemas ---

class ProfileBase(BaseModel):
    name: str
    base_url: str
    language: str
    crawling_strategy: str
    crawling_state: str = "not_started"
    is_active: bool = True


class ProfileCreate(ProfileBase):
    pass


class ProfileOut(ProfileBase):
    id: int

    class Config:
        from_attributes = True


# --- Article Schemas ---

class ArticleBase(BaseModel):
    url: str
    title: str
    author: Optional[str] = None
    content: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    classification: str
    sentiment: str
    thumbnail_url: Optional[str] = None
    tags: Optional[str] = None
    is_featured: bool = False
    is_reported: bool = False
    reported_reason: Optional[str] = None


class ArticleCreate(ArticleBase):
    source_id: int


class ArticleOut(ArticleBase):
    id: int
    source_id: int

    class Config:
        from_attributes = True


# Profile with nested articles
class ProfileWithArticles(ProfileOut):
    articles: List[ArticleOut] = []
