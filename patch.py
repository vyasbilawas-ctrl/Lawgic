with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'from database import Article, Session',
    'from database import Article, Session, Subscriber'
)

subscribe_code = '''
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

'''
code = code.replace('@app.route("/health")', subscribe_code + '@app.route("/health")')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
