from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    link = Column(String(500), unique=True)
    summary = Column(Text)
    image_url = Column(String(1000), default="")
    published_date = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100))
    category = Column(String(100), default="General News")

engine = create_engine('sqlite:///legal_news.db')

try:
    # Test if image_url column exists
    with engine.connect() as conn:
        conn.execute(text("SELECT image_url FROM articles LIMIT 1"))
except Exception:
    # Drop and recreate if schema is old
    Base.metadata.drop_all(engine)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
