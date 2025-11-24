from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./news.db"   # change to Postgres later

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # only for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
