with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

imports = '''
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from database import User, Bookmark
'''

code = code.replace('from database import Article, Session, Subscriber', imports + '\nfrom database import Article, Session, Subscriber')

init = '''
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

'''

code = code.replace('app = Flask(__name__)', 'app = Flask(__name__)\n' + init)

auth_routes = '''
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
'''

code = code.replace('@app.after_request', auth_routes + '\n@app.after_request')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
