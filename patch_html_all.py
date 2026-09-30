import re
import glob

# Add more feeds to scraper.py
with open('scraper.py', 'r', encoding='utf-8') as f:
    scraper_code = f.read()

more_sources = """RSS_FEEDS = {
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
}"""
scraper_code = re.sub(r'RSS_FEEDS = \{[^}]*\}', more_sources, scraper_code, flags=re.DOTALL)
with open('scraper.py', 'w', encoding='utf-8') as f:
    f.write(scraper_code)


# Add Home button and Animations to all templates
anim_css = """
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .article-card {
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            animation: fadeUp 0.6s ease-out forwards;
        }
        /* Delay animations for cards */
        .article-card:nth-child(1) { animation-delay: 0.1s; }
        .article-card:nth-child(2) { animation-delay: 0.2s; }
        .article-card:nth-child(3) { animation-delay: 0.3s; }
        .article-card:nth-child(4) { animation-delay: 0.4s; }
        .article-card:nth-child(5) { animation-delay: 0.5s; }
        
        .article-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(11, 37, 69, 0.1);
            border-left: 5px solid var(--accent);
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .hero {
            background: linear-gradient(-45deg, #f5f7fa, #ffffff, #eef2f7, #ffffff) !important;
            background-size: 400% 400% !important;
            animation: gradientShift 10s ease infinite !important;
        }
        .btn, button, .nav-link, .trend-item {
            transition: all 0.3s ease;
        }
        .btn:hover {
            transform: scale(1.05);
        }
        .trend-item:hover {
            transform: translateX(5px);
            background: #f0f4f8;
        }
        </style>
"""

files = ['templates/index.html', 'templates/bare_acts.html', 'templates/article.html', 'templates/profile.html', 'templates/ai_search.html']
for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            h = f.read()
        
        # Add Home button if not present
        if '<a class="nav-link" href="/"><i class="fas fa-home"></i>Home</a>' not in h:
            h = h.replace('<a class="nav-link" href="/bare-acts">', '<a class="nav-link" href="/"><i class="fas fa-home"></i>Home</a>\n              <a class="nav-link" href="/bare-acts">')
        
        # Add animations CSS if styling exists
        if '</style>' in h and 'fadeUp' not in h:
            h = h.replace('</style>', anim_css)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(h)
    except Exception as e:
        pass
