import os
import re
from datetime import datetime, timedelta

import feedparser
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from database import Article, Session

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 1. Direct Feeds & Google News Feeds
RSS_FEEDS = {
    "Google Legal (LiveLaw & BarBench)": "https://news.google.com/rss/search?q=site:livelaw.in+OR+site:barandbench.com+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
    "Google News (Supreme Court & High Court)": "https://news.google.com/rss/search?q=%22Supreme+Court+of+India%22+OR+%22High+Court%22+OR+%22BNS%22+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    "Bar and Bench": "https://www.barandbench.com/feed",
    "Verdictum": "https://www.verdictum.in/feed",
    "India Legal": "https://www.indialegallive.com/feed/",
    "Lawctopus": "https://www.lawctopus.com/feed/",
    "Supreme Court Observer": "https://www.scobserver.in/feed/"
}

# 2. Telegram Public Channels
TELEGRAM_CHANNELS = [
    {"source": "LiveLaw (Telegram)", "url": "https://t.me/s/livelawindia"},
    {"source": "Bar and Bench (Telegram)", "url": "https://t.me/s/barandbench"}
]

def parse_date(value):
    try:
        return date_parser.parse(value).replace(tzinfo=None) if value else datetime.utcnow()
    except (TypeError, ValueError, OverflowError):
        return datetime.utcnow()

def determine_category(title, summary):
    text = f"{title} {summary}".lower()
    if any(x in text for x in ("course", "certificate", "diploma", "admission", "scholarship", "university", "seminar", "webinar")):
        return "Courses & Education"
    if any(x in text for x in ("job", "vacancy", "recruitment", "hiring", "apply now", "interview")):
        return "Jobs & Opportunities"
    if any(x in text for x in ("supreme court", "cji", "sc judgment", "apex court")):
        return "Supreme Court"
    if any(x in text for x in ("high court", " hc ")):
        return "High Court"
    if any(x in text for x in ("murder", "rape", "bail", "criminal", "police", "fir", "ipc", "crpc", "bns")):
        return "Criminal Law"
    if any(x in text for x in ("tax", "corporate", "company", "business", "cci", "sebi", "insolvency", "ibc")):
        return "Corporate Law"
    if any(x in text for x in ("constitution", "fundamental right", "article 14", "article 21")):
        return "Constitutional Law"
    return "General News"

def entry_image(entry, category):
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
        
    # Fallbacks based on category
    if category == "Supreme Court":
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Supreme_Court_of_India_-_01.jpg/800px-Supreme_Court_of_India_-_01.jpg"
    elif category == "High Court":
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Bombay_High_Court.jpg/800px-Bombay_High_Court.jpg"
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
        prompt = f"""You are an expert Indian Legal Editor. Your job is to process raw news entries and format them perfectly.
Rules:
1. Provide an "Ideal Heading" (TITLE): Respectful, legally accurate, catchy.
2. Provide a "Head Note" (SUMMARY): 2-3 lines concise, lawful summary. If RAW SUMMARY is empty, generate from TITLE.
3. NEVER commit contempt of court.

RAW TITLE: {title}
RAW SUMMARY: {summary}

Output exactly:
TITLE: [Ideal Heading]
SUMMARY: [Head Note]"""
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

def scrape_telegram_channel(channel_info, session, recent_articles):
    total = 0
    try:
        resp = requests.get(channel_info["url"], headers={"User-Agent": USER_AGENT}, timeout=15)
        if resp.status_code != 200: return 0
        soup = BeautifulSoup(resp.content, "html.parser")
        messages = soup.find_all("div", class_="tgme_widget_message_wrap")
        for msg in messages[-10:]:
            try:
                text_div = msg.find("div", class_="tgme_widget_message_text")
                if not text_div: continue
                full_text = text_div.get_text(" ", strip=True)
                if len(full_text) < 40: continue

                date_anchor = msg.find("a", class_="tgme_widget_message_date")
                link = date_anchor["href"] if date_anchor and date_anchor.get("href") else ""
                if not link or session.query(Article.id).filter_by(link=link).first():
                    continue

                lines = full_text.split(".")
                raw_title = lines[0].strip()[:200]
                raw_summary = full_text[:800]

                # Deduplication check
                is_duplicate = False
                for existing in recent_articles:
                    if calculate_similarity(raw_title, existing.title) > 0.8:
                        is_duplicate = True
                        break
                if is_duplicate: continue

                title, summary = rewrite_with_gemini(raw_title, raw_summary)
                cat_name = determine_category(title, summary)

                # Extract photo if present
                img_url = ""
                photo_wrap = msg.find("a", class_="tgme_widget_message_photo_wrap")
                if photo_wrap and "style" in photo_wrap.attrs:
                    style = photo_wrap["style"]
                    m = re.search(r"background-image:url\('([^']+)'\)", style)
                    if m: img_url = m.group(1)

                if not img_url:
                    img_url = entry_image({}, cat_name)

                art = Article(
                    title=title,
                    link=link[:1000],
                    summary=summary,
                    image_url=img_url[:1000],
                    published_date=datetime.utcnow(),
                    source=channel_info["source"],
                    category=cat_name
                )
                
        # Automatically clean URLs from title before saving
        for var_name in ['article', 'new_article', 'item']:
            obj = locals().get(var_name)
            if obj and hasattr(obj, 'title') and obj.title:
                # Remove http:// or https:// or www.
                obj.title = re.sub(r'(?i)https?://\S+|www\.\S+', '', str(obj.title)).strip()
                # Remove any trailing colons or hyphens left behind (e.g. "News Title : " -> "News Title")
                obj.title = re.sub(r'[-:\|]+$', '', obj.title).strip()
        
        session.add(art)
                session.commit()
                recent_articles.append(art)
                total += 1
            except Exception as e:
                session.rollback()
    except Exception as e:
        print(f"Telegram scrape error: {e}")
    return total

def fetch_and_store_news():
    session = Session()
    total = 0
    try:
        recent_date = datetime.utcnow() - timedelta(days=3)
        recent_articles = session.query(Article).filter(Article.published_date >= recent_date).all()

        # Step 1: Scrape Telegram Public Channels
        for ch in TELEGRAM_CHANNELS:
            print(f"Fetching Telegram: {ch['source']}")
            total += scrape_telegram_channel(ch, session, recent_articles)

        # Step 2: Fetch RSS / Google News Feeds
        for source, url in RSS_FEEDS.items():
            print(f"Fetching {source}: {url}")
            try:
                response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
                response.raise_for_status()
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:20]:
                    try:
                        link = (entry.get("link") or "").strip()
                        if not link or session.query(Article.id).filter_by(link=link).first():
                            continue
                        title = (entry.get("title") or "Untitled legal update").strip()

                        # Deduplication check
                        is_duplicate = False
                        for existing in recent_articles:
                            if calculate_similarity(title, existing.title) > 0.8:
                                is_duplicate = True
                                exist_summary = existing.summary or ""
                                extra_link = f"<br><br><b>Also reported by {source}:</b> <a href='{link}' target='_blank'>Read here</a>"
                                if extra_link not in exist_summary:
                                    existing.summary = exist_summary + extra_link
                                    session.commit()
                                break
                        if is_duplicate:
                            continue

                        soup = BeautifulSoup(entry.get("summary", "") or "", "html.parser")
                        raw = soup.get_text(" ", strip=True)
                        summary = (raw[:997] + "...") if len(raw) > 1000 else (raw or "No summary available.")
                        title, summary = rewrite_with_gemini(title, summary)
                        cat_name = determine_category(title, summary)

                        art = Article(
                            title=title,
                            link=link[:1000],
                            summary=summary,
                            image_url=entry_image(entry, cat_name)[:1000],
                            published_date=parse_date(entry.get("published") or entry.get("updated")),
                            source=source,
                            category=cat_name
                        )
                        
        # Automatically clean URLs from title before saving
        for var_name in ['article', 'new_article', 'item']:
            obj = locals().get(var_name)
            if obj and hasattr(obj, 'title') and obj.title:
                # Remove http:// or https:// or www.
                obj.title = re.sub(r'(?i)https?://\S+|www\.\S+', '', str(obj.title)).strip()
                # Remove any trailing colons or hyphens left behind (e.g. "News Title : " -> "News Title")
                obj.title = re.sub(r'[-:\|]+$', '', obj.title).strip()
        
        session.add(art)
                        session.commit()
                        recent_articles.append(art)
                        total += 1
                        print(f"[{source}] Added: {title[:50]}")
                    except Exception as entry_err:
                        session.rollback()
            except Exception as feed_err:
                print(f"Error fetching {source}: {feed_err}")

        print(f"Scraping completed. Total new articles saved: {total}")
        return total
    finally:
        session.close()