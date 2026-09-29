import os
import atexit
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template, request
from sqlalchemy import or_, text

from database import Article, Session, Subscriber
from scraper import fetch_and_store_news

app = Flask(__name__)
scheduler = BackgroundScheduler(timezone="UTC")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def start_scheduler():
    if scheduler.running or not env_bool("ENABLE_SCHEDULER", False):
        return
    scheduler.add_job(fetch_and_store_news, "date", run_date=datetime.utcnow() + timedelta(seconds=10), id="initial-fetch", replace_existing=True)
    scheduler.add_job(fetch_and_store_news, "interval", minutes=max(5, int(os.getenv("NEWS_FETCH_MINUTES", "60"))), id="news-fetch", replace_existing=True, coalesce=True, max_instances=1)
    scheduler.start()


try:
    start_scheduler()
except Exception:
    app.logger.exception("Unable to start scheduler")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


atexit.register(shutdown_scheduler)


def clean_text(value, limit=2000):
    return str(value or "").strip()[:limit]


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.route("/")
def index():
    session = Session()
    try:
        category = clean_text(request.args.get("category"), 100)
        search = clean_text(request.args.get("q"), 200)
        query = session.query(Article)
        if category:
            query = query.filter(Article.category == category)
        if search:
            term = f"%{search}%"
            query = query.filter(or_(Article.title.ilike(term), Article.summary.ilike(term)))
        articles = query.order_by(Article.published_date.desc()).limit(50).all()
        categories = [row[0] for row in session.query(Article.category).filter(Article.category.isnot(None)).distinct().order_by(Article.category).all()]
        return render_template("index.html", articles=articles, categories=categories, current_cat=category, query=search)
    finally:
        session.close()


@app.route("/bare-acts")
def bare_acts():
    return render_template("bare_acts.html")


@app.route("/ai-search")
def ai_search():
    return render_template("ai_search.html")



@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    if "@" not in email or "." not in email:
        return jsonify({"error": "Invalid email address."}), 400
    
    session = Session()
    try:
        if session.query(Subscriber).filter_by(email=email).first():
            return jsonify({"message": "You are already subscribed!"}), 200
            
        session.add(Subscriber(email=email))
        session.commit()
        return jsonify({"message": "Successfully subscribed!"}), 200
    except Exception as e:
        session.rollback()
        app.logger.error(f"Error in subscribe: {e}")
        return jsonify({"error": "Unable to subscribe right now."}), 500
    finally:
        session.close()

@app.route("/health")
def health():
    session = Session()
    try:
        session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "scheduler": scheduler.running})
    finally:
        session.close()


@app.route("/api/ask-ai", methods=["POST"])
def ask_ai():
    data = request.get_json(silent=True) or {}
    query = clean_text(data.get("query"), 2000)
    language = "Hindi" if str(data.get("language", "English")).lower().startswith("hi") else "English"
    if not query:
        return jsonify({"error": "Please enter a legal question."}), 400
    api_key = os.getenv("GEMINI_SEARCH_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "AI service is not configured. Please add GEMINI_API_KEY."}), 503
    try:
        import bleach
        import google.generativeai as genai
        import markdown

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-3.5-flash"))
        prompt = f"""You are Lawgic's careful Indian legal research assistant. Answer in {language}.
Answer this question: {query}

Give a clear, neutral answer based on Indian law. Use markdown for formatting (e.g. **bold**, lists).
Explain that this is general information, not legal advice. Do not invent citations. If uncertain, say so.
At the end, list 2-4 relevant real judgments only when you are confident they are relevant, with the case name and one-sentence holding."""
        response = model.generate_content(prompt, request_options={"timeout": 120})
        answer = getattr(response, "text", "").strip()
        if not answer:
            raise ValueError("The AI returned an empty response")
            
        html_answer = markdown.markdown(answer)
        answer = bleach.clean(
            html_answer,
            tags=["p", "br", "strong", "ul", "ol", "li", "em", "b", "i", "h1", "h2", "h3", "h4", "h5", "h6"],
            attributes={},
            strip=True,
        )
        return jsonify({"response": answer})
    except Exception:
        app.logger.exception("AI request failed")
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
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=env_bool("FLASK_DEBUG", False))
