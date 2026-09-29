import os
import feedparser
import google.generativeai as genai
from datetime import datetime
from database import Session, Article
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Gemini API (it will use GEMINI_API_KEY from .env)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

RSS_FEEDS = {
    'LiveLaw': 'https://www.livelaw.in/rss',
    'Bar and Bench': 'https://www.barandbench.com/rss'
}

def parse_date(date_str):
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except:
        return datetime.now()

def determine_category(title, summary):
    text = (title + " " + summary).lower()
    if 'supreme court' in text or 'cji' in text or 'sc ' in text:
        return "Supreme Court"
    elif 'high court' in text or ' hc ' in text:
        return "High Court"
    elif 'murder' in text or 'rape' in text or 'bail' in text or 'criminal' in text or 'police' in text:
        return "Criminal Law"
    elif 'tax' in text or 'corporate' in text or 'company' in text or 'business' in text or 'cci' in text or 'sebi' in text:
        return "Corporate Law"
    elif 'constitution' in text or 'fundamental rights' in text or 'article' in text:
        return "Constitutional Law"
    return "General News"

def rewrite_with_gemini(title, summary):
    # If no API key, return original text
    if not os.environ.get("GEMINI_API_KEY"):
        return title, summary
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are an expert legal journalist. Please rewrite the following news title and summary to make it completely unique, engaging, and professional. 
        Do not change the factual meaning or the verdict. Keep it objective. Avoid plagiarism.
        
        Original Title: {title}
        Original Summary: {summary}
        
        Format your response exactly as:
        TITLE: [Your new title]
        SUMMARY: [Your new summary, around 3-4 sentences]
        """
        response = model.generate_content(prompt)
        text = response.text
        
        # Parse the response
        new_title = title
        new_summary = summary
        
        for line in text.split('\n'):
            if line.startswith('TITLE:'):
                new_title = line.replace('TITLE:', '').strip()
            elif line.startswith('SUMMARY:'):
                new_summary = line.replace('SUMMARY:', '').strip()
                
        return new_title, new_summary
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return title, summary

def fetch_and_store_news():
    session = Session()
    print(f"[{datetime.now()}] Starting news fetch...")
    
    for source, url in RSS_FEEDS.items():
        print(f"Fetching from {source}...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.get('link', '')
                existing = session.query(Article).filter_by(link=link).first()
                if not existing:
                    original_title = entry.get('title', '')
                    summary_html = entry.get('summary', '')
                    original_summary = BeautifulSoup(summary_html, 'html.parser').get_text()[:500] + '...'
                    
                    # REWRITE CONTENT USING AI
                    title, summary_text = rewrite_with_gemini(original_title, original_summary)
                    
                    category = determine_category(title, summary_text)
                    
                    published_str = entry.get('published', '')
                    pub_date = parse_date(published_str)
                    
                    article = Article(
                        title=title,
                        link=link,
                        summary=summary_text,
                        published_date=pub_date,
                        source=source,
                        category=category
                    )
                    session.add(article)
            session.commit()
            print(f"Finished fetching from {source}.")
        except Exception as e:
            print(f"Error fetching from {source}: {e}")
            session.rollback()
    
    session.close()

if __name__ == '__main__':
    fetch_and_store_news()
