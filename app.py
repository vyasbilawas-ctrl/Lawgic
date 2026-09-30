import os
import atexit
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template, request
from sqlalchemy import or_, text


from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from database import User, Bookmark

from database import Article, Session, Subscriber
from scraper import fetch_and_store_news

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-lawgic")
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    session = Session()
    try:
        return session.query(User).get(int(user_id))
    finally:
        session.close()


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



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        session = Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password_hash, password):
                login_user(user)
                return jsonify({"status": "success", "redirect": "/"})
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
        finally:
            session.close()
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        session = Session()
        try:
            if session.query(User).filter_by(username=username).first():
                return jsonify({"status": "error", "message": "Username already taken"}), 400
            
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, password_hash=hashed)
            session.add(user)
            session.commit()
            login_user(user)
            return jsonify({"status": "success", "redirect": "/"})
        finally:
            session.close()
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/api/bookmark/<int:article_id>", methods=["POST"])
@login_required
def toggle_bookmark(article_id):
    session = Session()
    try:
        bm = session.query(Bookmark).filter_by(user_id=current_user.id, article_id=article_id).first()
        if bm:
            session.delete(bm)
            session.commit()
            return jsonify({"status": "removed"})
        else:
            session.add(Bookmark(user_id=current_user.id, article_id=article_id))
            session.commit()
            return jsonify({"status": "added"})
    finally:
        session.close()

@app.route("/profile")
@login_required
def profile():
    session = Session()
    try:
        bookmarks = session.query(Bookmark).filter_by(user_id=current_user.id).all()
        article_ids = [b.article_id for b in bookmarks]
        articles = session.query(Article).filter(Article.id.in_(article_ids)).all() if article_ids else []
        return render_template("profile.html", articles=articles)
    finally:
        session.close()


@app.route("/api/force-update")
def force_update():
    import threading
    threading.Thread(target=fetch_and_store_news).start()
    return "Update started in background!"


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
    
    # We are using ZeroLimitAI for the chat bot
    api_key = os.getenv("ZEROLIMIT_API_KEY", "zlai_0e5b7348f1dca79f1f57f056fee587b97609f5fef821cd6f834dd8810b75828c")
    try:
        import bleach
        import markdown
        from openai import OpenAI
        
        client = OpenAI(
            base_url="https://www.zerolimitai.com/api/v1",
            api_key=api_key
        )
        
        system_msg = f"You are Lawgic's careful Indian legal research assistant. Answer strictly in {language}. Give a clear, neutral answer based on Indian law. Use markdown."
        
        response = client.chat.completions.create(
            model="auto",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": query}
            ],
            max_tokens=1024
        )
        
        text = response.choices[0].message.content
        html = markdown.markdown(text, extensions=['fenced_code', 'tables'])
        safe_html = bleach.clean(html, tags=['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li', 'br', 'h1', 'h2', 'h3', 'h4', 'code', 'pre', 'blockquote'])
        return jsonify({"response": safe_html})
    except Exception as e:
                return jsonify({"error": f"AI error: {str(e)}"}), 500

@app.route("/judicial-exam")
def judicial_exam():
    return render_template("judicial_exam.html")

@app.route("/api/judicial-tutor", methods=["POST"])
def judicial_tutor():
    data = request.get_json(silent=True) or {}
    query = clean_text(data.get("query"), 3000)
    if not query:
        return jsonify({"error": "Please ask a legal question or provide an answer to check."}), 400
        
    api_key = os.getenv("ZEROLIMIT_API_KEY", "zlai_0e5b7348f1dca79f1f57f056fee587b97609f5fef821cd6f834dd8810b75828c")
    try:
        import bleach
        import markdown
        from openai import OpenAI
        
        client = OpenAI(
            base_url="https://www.zerolimitai.com/api/v1",
            api_key=api_key
        )
        
        system_msg = """You are the Lawgic Judicial Mastery AI, an expert judicial educator specialising in Indian law and judicial service exam preparation (like RHJS).
TEACHING STYLE: Judicial discipline, structured analysis, and examiner-oriented preparation.
LAW ACCURACY (CRITICAL): Always use NEW LAWS (BNS 2023, BNSS 2023, BSA 2023) for criminal matters. Do NOT cite old IPC/CrPC/IEA unless asked for historical context.
MANDATORY RULES FOR ANSWERS:
1. Always give the exact section number.
2. Break down the ingredients of the offence/provision.
3. Cite Landmark Supreme Court cases and, if possible, relevant High Court cases.
4. If comparing concepts, provide a 2-column distinction table.
5. Include a NEW vs OLD law quick reference table if discussing criminal law.
6. If the user asks you to 'check their answer', provide a Score, Gap Analysis, and a Topper Version.
You must adopt a mentor-like, encouraging yet strict tone to train them to think like a Judge."""

        response = client.chat.completions.create(
            model="auto",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": query}
            ],
            max_tokens=2048
        )
        
        text = response.choices[0].message.content
        html = markdown.markdown(text, extensions=['fenced_code', 'tables'])
        safe_html = bleach.clean(html, tags=['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li', 'br', 'h1', 'h2', 'h3', 'h4', 'code', 'pre', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td'])
        return jsonify({"response": safe_html})
    except Exception as e:
        return jsonify({"error": f"AI error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=env_bool("FLASK_DEBUG", False))
