import sqlite3
c = sqlite3.connect('legal_news.db')
print([r[0] for r in c.execute('SELECT image_url FROM articles WHERE source="Verdictum" LIMIT 5')])
