import os
from datetime import datetime

import feedparser
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from dotenv import load_dotenv

from database import Article, Session

load_dotenv()
RSS_FEEDS = {
    "Bar and Bench": "https://www.barandbench.com/feed",
    "Verdictum": "https://www.verdictum.in/feed",
    "Indian Kanoon SC": "https://indiankanoon.org/feeds/latest/supremecourt/",
}
USER_AGENT = "Lawgic/1.1 (+https://github.com/vyasbilawas-ctrl/Lawgic)"


def parse_date(value):
    try:
        return date_parser.parse(value).replace(tzinfo=None) if value else datetime.utcnow()
    except (TypeError, ValueError, OverflowError):
        return datetime.utcnow()


def determine_category(title, summary):
    text = f"{title} {summary}".lower()
    if any(x in text for x in ("supreme court", "cji", "sc judgment")): return "Supreme Court"
    if any(x in text for x in ("high court", " hc ")): return "High Court"
    if any(x in text for x in ("murder", "rape", "bail", "criminal", "police", "fir")): return "Criminal Law"
    if any(x in text for x in ("tax", "corporate", "company", "business", "cci", "sebi")): return "Corporate Law"
    if any(x in text for x in ("constitution", "fundamental right", "article 14", "article 21")): return "Constitutional Law"
    return "General News"


def entry_image(entry):
    for key in ("media_content", "media_thumbnail"):
        for item in entry.get(key, []) or []:
            url = item.get("url")
            if url: return url
    for enclosure in entry.get("enclosures", []) or []:
        if enclosure.get("href") and str(enclosure.get("type", "")).startswith("image/"):
            return enclosure["href"]
    soup = BeautifulSoup(entry.get("summary", "") or entry.get("content", ""), "html.parser")
    image = soup.find("img")
    return image.get("src", "") if image else ""


def rewrite_with_gemini(title, summary):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return title, summary
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_SCRAPER_MODEL", "gemini-1.5-flash"))
        prompt = f"""Rewrite this into a proper news format. If it is a raw court case (like from Indian Kanoon), give it a short catchy news heading (TITLE) and a clear, brief news summary of the case (SUMMARY). Return exactly TITLE: and SUMMARY: lines.
TITLE: {title}
SUMMARY: {summary}"""
        response = model.generate_content(prompt)
        new_title, new_summary = title, summary
        for line in getattr(response, "text", "").splitlines():
            if line.startswith("TITLE:"): new_title = line[6:].strip()
            elif line.startswith("SUMMARY:"): new_summary = line[8:].strip()
        return new_title[:500] or title, new_summary[:4000] or summary
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
                    if not link or session.query(Article.id).filter_by(link=link).first(): continue
                    title = (entry.get("title") or "Untitled legal update").strip()
                    soup = BeautifulSoup(entry.get("summary", "") or "", "html.parser")
                    raw = soup.get_text(" ", strip=True)
                    summary = (raw[:997] + "...") if len(raw) > 1000 else (raw or "No summary available.")
                    title, summary = rewrite_with_gemini(title, summary)
                    session.add(Article(title=title, link=link[:1000], summary=summary, image_url=entry_image(entry)[:1000], published_date=parse_date(entry.get("published") or entry.get("updated")), source=source, category=determine_category(title, summary)))
                    total += 1
                session.commit()
            except Exception:
                session.rollback()
        return total
    finally:
        session.close()
