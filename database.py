from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    link = Column(String(500), unique=True)
    summary = Column(Text)
    published_date = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100))
    category = Column(String(100), default="General News")

engine = create_engine('sqlite:///legal_news.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
