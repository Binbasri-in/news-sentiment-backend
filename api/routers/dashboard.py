from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Profile, Article

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ----- Profiles Management Page -----
@router.get("/profiles", response_class=HTMLResponse)
def profiles_dashboard(request: Request, db: Session = Depends(get_db)):
    profiles = db.query(Profile).all()
    return templates.TemplateResponse("profiles.html", {"request": request, "profiles": profiles})


# ----- Articles List Page (Crawling Results) -----
@router.get("/articles", response_class=HTMLResponse)
def articles_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    search: str = Query(None),
    classification: str = Query(None),
    sentiment: str = Query(None),
    tags: str = Query(None),
    is_featured: bool = Query(None),
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(Article)

    if search:
        search_term = f"%{search}%"
        query = query.filter((Article.title.ilike(search_term)) | (Article.content.ilike(search_term)))
    if classification:
        query = query.filter(Article.classification == classification)
    if sentiment:
        query = query.filter(Article.sentiment == sentiment)
    if tags:
        tags_list = [tag.strip().lower() for tag in tags.split(",")]
        for tag in tags_list:
            query = query.filter(Article.tags.ilike(f"%{tag}%"))
    if is_featured is not None:
        query = query.filter(Article.is_featured == is_featured)

    articles = query.offset(skip).limit(limit).all()

    return templates.TemplateResponse("articles.html", {"request": request, "articles": articles})


# ----- Article Detail Page -----
@router.get("/articles/{article_id}", response_class=HTMLResponse)
def article_detail(article_id: int, request: Request, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return templates.TemplateResponse("article_detail.html", {"request": request, "article": article})


# ----- Report Article Form Page -----
@router.get("/articles/{article_id}/report", response_class=HTMLResponse)
def article_report_form(article_id: int, request: Request, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return templates.TemplateResponse("article_report.html", {"request": request, "article": article})


# ----- Section 3 Page -----
@router.get("/section3", response_class=HTMLResponse)
def section3_dashboard(request: Request):
    return templates.TemplateResponse("section3.html", {"request": request})


# ----- Section 4 Page -----
@router.get("/section4", response_class=HTMLResponse)
def section4_dashboard(request: Request):
    return templates.TemplateResponse("section4.html", {"request": request})
