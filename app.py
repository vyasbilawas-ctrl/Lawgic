from flask import Flask, render_template, request
from database import Session, Article
from scraper import fetch_and_store_news
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from sqlalchemy import or_

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_and_store_news, trigger="interval", minutes=60)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    session = Session()
    category_filter = request.args.get('category')
    search_query = request.args.get('q')
    
    query = session.query(Article)
    
    if category_filter:
        query = query.filter(Article.category == category_filter)
    if search_query:
        query = query.filter(or_(Article.title.ilike(f'%{search_query}%'), Article.summary.ilike(f'%{search_query}%')))
        
    articles = query.order_by(Article.published_date.desc()).limit(50).all()
    
    # Get unique categories for sidebar
    categories = [cat[0] for cat in session.query(Article.category).distinct().all()]
    
    session.close()
    return render_template('index.html', articles=articles, categories=categories, current_cat=category_filter, query=search_query)

if __name__ == '__main__':
    # Initial fetch before running
    fetch_and_store_news()
    app.run(debug=True, use_reloader=False)
