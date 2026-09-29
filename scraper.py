import os
from datetime import datetime

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from dotenv import load_dotenv
import feedparser
import google.generativeai as genai
import requests

from database import Article, Session

load_dotenv()

RSS_FEEDS = {
    "Bar and Bench": "https://www.barandbench.com/feed",
    "Verdictum": "https://www.verdictum.in/feed",
    "Indian Kanoon SC": "https://indiankanoon.org/feeds/latest/supremecourt/",
}
USER_AGENT = "Lawgic/1.0 (+https://github.com/vyasbilawas-ctrl/Lawgic)"


def parse_date(value):
    try:
        return date_parser.parse(value).replace(tzinfo=None) if value else datetime.utcnow()
    except (TypeError, ValueError, OverflowError):
        return datetime.utcnow()


def determine_category(title, summary):
    text = f"{title} {summary}".lower()
    if any(word in text for word in ("supreme court", "cji", "sc judgment")):
        return "Supreme Court"
    if any(word in text for word in ("high court", " hc ")):
        return "High Court"
    if any(word in text for word in ("murder", "rape", "bail", "criminal", "police", "fir")):
        return "Criminal Law"
    if any(word in text for word in ("tax", "corporate", "company", "business", "cci", "sebi")):
        return "Corporate Law"
    if any(word in text for word in ("constitution", "fundamental right", "article 14", "article 21")):
        return "Constitutional Law"
    return "General News"


def rewrite_with_gemini(title, summary):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return title, summary
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_SCRAPER_MODEL", "gemini-1.5-flash"))
        response = model.generate_content(
            f"Rewrite this Indian legal news objectively without changing facts. Return exactly two lines: TITLE: ... and SUMMARY: ...\nTITLE: {title}\nSUMMARY: {summary}"
        )
        new_title, new_summary = title, summary
        for line in getattr(response, "text", "").splitlines():
            if line.startswith("TITLE:"):
                new_title = line[6:].strip()[:500] or title
            elif line.startswith("SUMMARY:"):
                new_summary = line[8:].strip()[:4000] or summary
        return new_title, new_summary
    except Exception:
        return title, summary


def fetch_and_store_news():
    session = Session()
    total = 0
    try:
        for source, url in RSS_FEEDS.items():
            try:
                response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
                response.raise_for_status()
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:50]:
                    link = (entry.get("link") or "").strip()
                    title = (entry.get("title") or "Untitled legal update").strip()
                    if not link or session.query(Article.id).filter_by(link=link).first():
                        continue
                    text = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)
                    summary = (text[:997] + "...") if len(text) > 1000 else (text or "No summary available.")
                    title, summary = rewrite_with_gemini(title, summary)
                    media = entry.get("media_content") or []
                    image_url = media[0].get("url", "") if media else ""
                    session.add(Article(title=title[:500], link=link[:1000], summary=summary, image_url=image_url[:1000], published_date=parse_date(entry.get("published") or entry.get("updated")), source=source, category=determine_category(title, summary)))
                    total += 1
                session.commit()
            except Exception:
                session.rollback()
        return total
    finally:
        session.close()


if __name__ == "__main__":
    print(f"Stored {fetch_and_store_news()} new articles")
