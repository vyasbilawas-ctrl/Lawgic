import re
with open('scraper.py', 'r', encoding='utf-8') as f:
    code = f.read()

sources = """RSS_FEEDS = {
    "Bar and Bench": "https://www.barandbench.com/feed",
    "Verdictum": "https://www.verdictum.in/feed",
    "Indian Kanoon SC": "https://indiankanoon.org/feeds/latest/supremecourt/",
    "Live Law": "https://www.livelaw.in/feed/",
    "India Legal": "https://www.indialegallive.com/feed/",
    "Supreme Court Observer": "https://www.scobserver.in/feed/"
}"""

code = re.sub(r'RSS_FEEDS = \{[^}]*\}', sources, code, flags=re.DOTALL)
with open('scraper.py', 'w', encoding='utf-8') as f:
    f.write(code)
