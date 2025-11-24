from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from backend.app.db.session import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    text = Column(Text)
    published_date = Column(DateTime, default=func.now())
    topic_id = Column(Integer, nullable=True)

    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)
