with open('database.py', 'r', encoding='utf-8') as f:
    code = f.read()

user_code = '''
from flask_login import UserMixin

class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Bookmark(Base):
    __tablename__ = "bookmarks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    article_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
'''

code = code.replace(
    'class Subscriber(Base):',
    user_code + '\nclass Subscriber(Base):'
)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(code)
