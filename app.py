from flask import Flask, render_template, request, jsonify
from database import Session, Article
from scraper import fetch_and_store_news
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import atexit
from sqlalchemy import or_

app = Flask(__name__)

scheduler = BackgroundScheduler()


def start_scheduler():
    if scheduler.running:
        return

    # Run once shortly after startup, then continue every hour.
    # The previous version used a bare `trigger="date"` without `run_date`,
    # which causes APScheduler to fail during app startup.
    scheduler.add_job(
        func=fetch_and_store_news,
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=5),
    )
    scheduler.add_job(
        func=fetch_and_store_news,
        trigger="interval",
        hours=1,
    )
    scheduler.start()


start_scheduler()
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


@app.route('/bare-acts')
def bare_acts():
    return render_template('bare_acts.html')


@app.route('/ai-search')
def ai_search():
    return render_template('ai_search.html')


@app.route('/api/ask-ai', methods=['POST'])
def ask_ai():
    data = request.get_json(silent=True) or {}
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'Query is empty'}), 400

    try:
        import google.generativeai as genai
        import os

        # Use a separate key for search if available, to avoid rate limits from the scraper
        search_api_key = os.environ.get("GEMINI_SEARCH_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
        if not search_api_key:
            return jsonify({'error': 'Gemini API key is not configured'}), 500

        genai.configure(api_key=search_api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')

        prompt = f"""
        You are an expert Indian Legal AI Assistant on the Lawgic platform.
        A user has asked the following legal query: "{query}"

        Please provide a comprehensive but easy-to-understand answer based on Indian Law.
        Structure your answer using HTML tags (<br>, <b>, <ul>, <li>) for formatting.
        Do not use markdown like **bold**, use HTML <b>bold</b> instead.

        Crucially, at the end of your answer, you MUST provide a list of 2-4 real, landmark Indian Supreme Court or High Court judgments relevant to this query.
        For each judgment, provide the case name and a 1-sentence summary of what was held.
        """

        response = model.generate_content(prompt)
        return jsonify({'response': response.text})
    except Exception as e:
        print("AI Error:", e)
        return jsonify({'error': 'Failed to process request. Please try again later.'}), 500


@app.route('/article/<int:id>')
def article_page(id):
    session = Session()
    article = session.query(Article).filter_by(id=id).first()
    session.close()
    if article:
        return render_template('article.html', article=article)
    return "Article not found", 404


if __name__ == '__main__':
    # Initial fetch before running
    fetch_and_store_news()
    app.run(debug=True, use_reloader=False)
