# backend/app/routes/article.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from backend.app.db.session import SessionLocal
from backend.app.db.models.article import Article

router = APIRouter()

class ArticleOut(BaseModel):
    id: int
    title: str | None
    text: str | None
    # match the DB type (datetime) so pydantic can validate ORM objects
    published_date: datetime | None
    topic_id: int | None
    summary: str | None
    key_points: List[str] | None

    # Pydantic v2: use `from_attributes` to read ORM objects
    model_config = {"from_attributes": True}

@router.get("/", response_model=List[ArticleOut])
def list_articles(limit: int = 50):
    db = SessionLocal()
    try:
        articles = db.query(Article).order_by(Article.published_date.desc()).limit(limit).all()
        return articles
    finally:
        db.close()

@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: int):
    db = SessionLocal()
    try:
        art = db.query(Article).filter(Article.id == article_id).first()
        if not art:
            raise HTTPException(status_code=404, detail="Article not found")
        return art
    finally:
        db.close()
