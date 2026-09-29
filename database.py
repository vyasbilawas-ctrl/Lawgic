import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=False, default="")
    image_url = Column(String(1000), default="")
    published_date = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(100), nullable=False, default="Unknown")
    category = Column(String(100), default="General News", index=True)

class Subscriber(Base):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///legal_news.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

# Create missing columns without destroying existing articles.
Base.metadata.create_all(engine)
if DATABASE_URL.startswith("sqlite"):
    existing = {column["name"] for column in inspect(engine).get_columns("articles")}
    for name, definition in {"image_url": "VARCHAR(1000)", "category": "VARCHAR(100)"}.items():
        if name not in existing:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE articles ADD COLUMN {name} {definition}"))

Session = sessionmaker(bind=engine, expire_on_commit=False)
