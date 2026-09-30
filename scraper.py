import os
from datetime import datetime, timedelta
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
    
    "India Legal": "https://www.indialegallive.com/feed/",
    "Supreme Court Observer": "https://www.scobserver.in/feed/",
    "Lawctopus": "https://www.lawctopus.com/feed/",
    
    
    
    
}
USER_AGENT = "Lawgic/1.1 (+https://github.com/vyasbilawas-ctrl/Lawgic)"


def parse_date(value):
    try:
        return date_parser.parse(value).replace(tzinfo=None) if value else datetime.utcnow()
    except (TypeError, ValueError, OverflowError):
        return datetime.utcnow()


def determine_category(title, summary):
    text = f"{title} {summary}".lower()
    if any(x in text for x in ("course", "certificate", "diploma", "admission", "scholarship", "university", "seminar", "webinar")): return "Courses & Education"
    if any(x in text for x in ("job", "vacancy", "recruitment", "hiring", "apply now", "interview")): return "Jobs & Opportunities"
    if any(x in text for x in ("supreme court", "cji", "sc judgment", "apex court")): return "Supreme Court"
    if any(x in text for x in ("high court", " hc ")): return "High Court"
    if any(x in text for x in ("murder", "rape", "bail", "criminal", "police", "fir", "ipc", "crpc", "bns")): return "Criminal Law"
    if any(x in text for x in ("tax", "corporate", "company", "business", "cci", "sebi", "insolvency", "ibc")): return "Corporate Law"
    if any(x in text for x in ("constitution", "fundamental right", "article 14", "article 21")): return "Constitutional Law"
    return "General News"



def entry_image(entry, category):
    # Try finding image in feed
    for key in ("media_content", "media_thumbnail"):
        for item in entry.get(key, []) or []:
            url = item.get("url")
            if url: return url
    for enclosure in entry.get("enclosures", []) or []:
        if enclosure.get("href") and str(enclosure.get("type", "")).startswith("image/"):
            return enclosure["href"]
    soup = BeautifulSoup(entry.get("summary", "") or entry.get("content", ""), "html.parser")
    image = soup.find("img")
    if image and image.get("src"):
        return image.get("src")
        
    # AI Fallback based on category
    if category == "Supreme Court":
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Supreme_Court_of_India_-_01.jpg/800px-Supreme_Court_of_India_-_01.jpg"
    elif category == "High Court":
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Bombay_High_Court.jpg/800px-Bombay_High_Court.jpg"
    elif category == "Criminal Law":
        return "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?auto=format&fit=crop&q=80&w=800"
    elif category == "Corporate Law":
        return "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&q=80&w=800"
    else:
        return "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?auto=format&fit=crop&q=80&w=800"



def rewrite_with_gemini(title, summary):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return title, summary
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_SCRAPER_MODEL", "gemini-3.5-flash"))
        prompt = f"""You are an expert Indian Legal Editor. Your job is to process raw RSS feed entries and format them perfectly.
Please follow these STRICT rules:
1. Provide an "Ideal Heading" (TITLE): Professional, respectful, legally accurate, and catchy.
2. Provide a "Head Note" (SUMMARY): A clear, concise summary of the case/news. If the RAW SUMMARY is empty, short, or says "No summary available.", you MUST generate a logical summary/headnote based solely on the RAW TITLE.
3. NEVER commit contempt of court.

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


def calculate_similarity(t1, t2):
    stop_words = {"to", "of", "in", "for", "on", "with", "at", "by", "from", "up", "about", "into", "over", "after", "the", "a", "an", "and", "or", "is", "are", "was", "were", "court", "high", "supreme", "plea"}
    w1 = set(re.findall(r'\w+', t1.lower())) - stop_words
    w2 = set(re.findall(r'\w+', t2.lower())) - stop_words
    if not w1 or not w2: return 0
    return len(w1.intersection(w2)) / max(len(w1), len(w2))

def fetch_and_store_news():
    session = Session()
    total = 0
    try:
        recent_date = datetime.utcnow() - timedelta(days=3)
        recent_articles = session.query(Article).filter(Article.published_date >= recent_date).all()
        for source, url in RSS_FEEDS.items():
            try:
                response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
                response.raise_for_status()
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:30]:
                    link = (entry.get("link") or "").strip()
                    if not link or session.query(Article.id).filter_by(link=link).first(): continue
                    title = (entry.get("title") or "Untitled legal update").strip()
                    
                    is_duplicate = False
                    for existing in recent_articles:
                        if calculate_similarity(title, existing.title) > 0.75:
                            is_duplicate = True
                            extra_link = f"<br><br><b>Also reported by {source}:</b> <a href='{link}' target='_blank'>Read here</a>"
                            if extra_link not in existing.summary:
                                existing.summary += extra_link
                                session.add(existing)
                            break
                    if is_duplicate: continue
                    
                    soup = BeautifulSoup(entry.get("summary", "") or "", "html.parser")
                    raw = soup.get_text(" ", strip=True)
                    summary = (raw[:997] + "...") if len(raw) > 1000 else (raw or "No summary available.")
                    title, summary = rewrite_with_gemini(title, summary)
                    cat_name = determine_category(title, summary)
                    session.add(Article(title=title, link=link[:1000], summary=summary, image_url=entry_image(entry, cat_name)[:1000], published_date=parse_date(entry.get("published") or entry.get("updated")), source=source, category=cat_name))
                    total += 1
                session.commit()
            except Exception:
                session.rollback()
        return total
    finally:
        session.close()
