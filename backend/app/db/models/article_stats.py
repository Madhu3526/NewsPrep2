from sqlalchemy import Column, Integer
from backend.app.db.session import Base

class ArticleStats(Base):
    __tablename__ = "article_stats"

    article_id = Column(Integer, primary_key=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    bookmarks = Column(Integer, default=0)
