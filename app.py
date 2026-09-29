import atexit
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template, request
from sqlalchemy import or_

from database import Article, Session
from scraper import fetch_and_store_news

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler():
    """Start one safe scheduler instance for deployments that enable it."""
    if scheduler.running or os.getenv("ENABLE_SCHEDULER", "true").lower() not in {"1", "true", "yes"}:
        return

    scheduler.add_job(
        fetch_and_store_news,
        trigger="date",
        run_date=datetime.utcnow() + timedelta(seconds=10),
        id="initial-news-fetch",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        fetch_and_store_news,
        trigger="interval",
        minutes=int(os.getenv("NEWS_FETCH_MINUTES", "60")),
        id="hourly-news-fetch",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=900,
    )
    scheduler.start()


start_scheduler()
atexit.register(lambda: scheduler.shutdown(wait=False) if scheduler.running else None)


def get_clean_query(value, max_length=500):
    return (value or "").strip()[:max_length]


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.route("/")
def index():
    session = Session()
    try:
        category_filter = get_clean_query(request.args.get("category"), 100)
        search_query = get_clean_query(request.args.get("q"))
        query = session.query(Article)
        if category_filter:
            query = query.filter(Article.category == category_filter)
        if search_query:
            term = f"%{search_query}%"
            query = query.filter(or_(Article.title.ilike(term), Article.summary.ilike(term)))
        articles = query.order_by(Article.published_date.desc()).limit(50).all()
        categories = [row[0] for row in session.query(Article.category).filter(Article.category.isnot(None)).distinct().order_by(Article.category).all()]
        return render_template("index.html", articles=articles, categories=categories, current_cat=category_filter, query=search_query)
    finally:
        session.close()


@app.route("/bare-acts")
def bare_acts():
    return render_template("bare_acts.html")


@app.route("/ai-search")
def ai_search():
    return render_template("ai_search.html")


@app.route("/health")
def health():
    session = Session()
    try:
        session.execute(__import__("sqlalchemy").text("SELECT 1"))
        return jsonify({"status": "ok"})
    finally:
        session.close()


@app.route("/api/ask-ai", methods=["POST"])
def ask_ai():
    data = request.get_json(silent=True) or {}
    query = get_clean_query(data.get("query"), 2000)
    if not query:
        return jsonify({"error": "Please enter a legal question."}), 400

    api_key = os.getenv("GEMINI_SEARCH_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "AI service is not configured. Please add GEMINI_API_KEY."}), 503

    try:
        import bleach
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-pro"))
        prompt = f"""You are Lawgic's careful Indian legal research assistant.
Answer this question: {query}

Give a clear, neutral answer based on Indian law. Use only these HTML tags: <p>, <br>, <strong>, <ul>, <ol>, <li>.
Explain that this is general information, not legal advice. Do not invent citations. If uncertain, say so.
At the end, list 2-4 relevant real judgments only when you are confident they are relevant, with the case name and one-sentence holding."""
        response = model.generate_content(prompt)
        answer = getattr(response, "text", "").strip()
        if not answer:
            raise ValueError("The AI returned an empty response")
        answer = bleach.clean(answer, tags=["p", "br", "strong", "ul", "ol", "li"], attributes={}, strip=True)
        return jsonify({"response": answer})
    except Exception as exc:
        app.logger.exception("AI request failed: %s", exc)
        return jsonify({"error": "Unable to process the request right now. Please try again."}), 502


@app.route("/article/<int:id>")
def article_page(id):
    session = Session()
    try:
        article = session.query(Article).filter_by(id=id).first()
        if not article:
            return render_template("404.html"), 404
        return render_template("article.html", article=article)
    finally:
        session.close()


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
