import re

with open('app.py', 'r', encoding='utf-8') as f:
    h = f.read()

update_route = """
@app.route("/api/force-update")
def force_update():
    import threading
    threading.Thread(target=scraper.fetch_and_store_news).start()
    return "Update started in background!"

"""

if 'force_update' not in h:
    h = h.replace('@app.after_request', update_route + '\n@app.after_request')
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(h)
