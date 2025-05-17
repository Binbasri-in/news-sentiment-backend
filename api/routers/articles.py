from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from sqlalchemy import or_

from api.database import get_db
from api.models import Article, Profile
from api.schemas import ArticleCreate, ArticleOut
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ArticleOut)
def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    existing = db.query(Article).filter(Article.url == article.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Article with this URL already exists")

    profile = db.query(Profile).filter(Profile.id == article.source_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Associated profile not found")

    new_article = Article(**article.dict())
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    return new_article

def split_filter_list(values: Optional[List[str]]) -> List[str]:
    if not values:
        return []
    result = []
    for val in values:
        result.extend([v.strip() for v in val.split(",") if v.strip()])
    return result

@router.get("/", response_model=List[ArticleOut])
def get_articles(
    db: Session = Depends(get_db),
    profile_id: Optional[int] = Query(None),
    classification: Optional[List[str]] = Query(None),
    sentiment: Optional[List[str]] = Query(None),
    ministry: Optional[List[str]] = Query(None),
    tags: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 20,
):
    logger.debug("Fetching articles with filters: %s", {
        "profile_id": profile_id,
        "classification": classification,
        "sentiment": sentiment,
        "ministry": ministry,
        "tags": tags,
        "search": search,
        "is_featured": is_featured,
        "skip": skip,
        "limit": limit
    })

    query = db.query(Article)

    if profile_id:
        query = query.filter(Article.source_id == profile_id)

    cls_list = split_filter_list(classification)
    if cls_list:
        query = query.filter(or_(*[Article.classification.ilike(c) for c in cls_list]))

    sent_list = split_filter_list(sentiment)
    if sent_list:
        query = query.filter(or_(*[Article.sentiment.ilike(s) for s in sent_list]))

    min_list = split_filter_list(ministry)
    if min_list:
        query = query.filter(or_(*[Article.ministry_to_report.ilike(m) for m in min_list]))

    if tags:
        tags_list = [tag.strip().lower() for tag in tags.split(",")]
        for tag in tags_list:
            query = query.filter(Article.tags.ilike(f"%{tag}%"))

    if search:
        search_term = f"%{search}%"
        query = query.filter((Article.title.ilike(search_term)) | (Article.content.ilike(search_term)))

    if is_featured is not None:
        query = query.filter(Article.is_featured == is_featured)

    logger.debug("Number of Results: %d", query.count())
    return query.offset(skip).limit(limit).all()


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.put("/{article_id}", response_model=ArticleOut)
def update_article(article_id: int, article_update: ArticleCreate, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    profile = db.query(Profile).filter(Profile.id == article_update.source_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Associated profile not found")

    for key, value in article_update.dict().items():
        setattr(article, key, value)

    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    db.delete(article)
    db.commit()
    return {"message": f"Article with ID {article_id} deleted successfully."}


# 🆕 NEW: Report an Article
@router.post("/{article_id}/report", response_model=ArticleOut)
def report_article(article_id: int, reason: dict, db: Session = Depends(get_db)):
    print(reason)
    reason = reason.get("params")
    reason = reason.get("reason")
    
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_reported = True
    article.reported_reason = reason

    db.commit()
    db.refresh(article)
    print(article)
    return article


# 🆕 NEW: List Reported Articles (for Admin review maybe)
@router.get("/reported/", response_model=List[ArticleOut])
def get_reported_articles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    articles = db.query(Article).filter(Article.is_reported == True).offset(skip).limit(limit).all()
    return articles

