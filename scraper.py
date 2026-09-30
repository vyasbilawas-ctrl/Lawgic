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
    "Live Law": "https://www.livelaw.in/feed/",
    "India Legal": "https://www.indialegallive.com/feed/",
    "Supreme Court Observer": "https://www.scobserver.in/feed/",
    "Lawctopus": "https://www.lawctopus.com/feed/",
    "Legally India": "https://www.legallyindia.com/feed",
    "Livelaw News": "https://www.livelaw.in/xml/top-stories.xml",
    "PathLegal": "https://www.pathlegal.in/rss.php",
    "LatestLaws": "https://www.latestlaws.com/rss-feeds/latest-news"
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
        model = genai.GenerativeModel(os.getenv("GEMINI_SCRAPER_MODEL", "gemini-3.5-flash"))
        prompt = f"""You are an expert Indian Legal Editor. Your job is to process raw RSS feed entries, especially from Indian Kanoon or other raw legal feeds, and format them perfectly.
Please follow these STRICT rules to avoid contempt of court and ensure accurate legal reporting:
1. Provide an "Ideal Heading" (TITLE): It should be professional, respectful to the courts, legally accurate, and catchy but not sensationalist.
2. Provide a "Head Note" (SUMMARY): A clear, concise, and lawful summary of the judgment/news. If the input is just a case name with no summary, infer the general nature of the case or provide a standard neutral headnote template.
3. NEVER commit contempt of court. Always use respectful language for the judiciary.

Input Data:
RAW TITLE: {title}
RAW SUMMARY: {summary}

Output exactly in this format:
TITLE: [Your Ideal Heading]
SUMMARY: [Your Head Note]
"""
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
