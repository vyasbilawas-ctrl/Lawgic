import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Remove Hero Section
h = re.sub(r'<header class="hero".*?</header>', '', h, flags=re.DOTALL)

# Remove Search Shell
h = re.sub(r'<div class="container-lg">\s*<div class="search-shell">.*?</div>\s*</div>', '', h, flags=re.DOTALL)

# Update Animations for Luxury Awwwards Feel
new_animations = """
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(40px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .article-card {
            transition: transform 0.6s cubic-bezier(0.165, 0.84, 0.44, 1), box-shadow 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
            animation: fadeUp 0.8s cubic-bezier(0.165, 0.84, 0.44, 1) forwards;
            opacity: 0;
            overflow: hidden;
            position: relative;
            background: white;
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.04);
            box-shadow: 0 4px 20px rgba(0,0,0,0.03);
            display: flex;
            gap: 18px;
        }
        /* Delay animations for cards */
        .article-card:nth-child(1) { animation-delay: 0.1s; }
        .article-card:nth-child(2) { animation-delay: 0.2s; }
        .article-card:nth-child(3) { animation-delay: 0.3s; }
        .article-card:nth-child(4) { animation-delay: 0.4s; }
        .article-card:nth-child(5) { animation-delay: 0.5s; }
        
        .article-card:hover {
            transform: scale(1.025) translateY(-8px);
            box-shadow: 0 40px 80px rgba(11, 37, 69, 0.15);
            border-color: transparent;
            z-index: 10;
        }

        .article-thumb {
            transition: transform 0.8s cubic-bezier(0.165, 0.84, 0.44, 1);
        }
        
        .article-card:hover .article-thumb {
            transform: scale(1.1);
        }

        .featured-card {
            transition: transform 0.6s cubic-bezier(0.165, 0.84, 0.44, 1), box-shadow 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
            overflow: hidden;
        }
        
        .featured-card:hover {
            transform: scale(1.02);
            box-shadow: 0 40px 80px rgba(11, 37, 69, 0.15);
        }
        
        .featured-card:hover .featured-img {
            transform: scale(1.08);
        }
        
        .featured-img {
            transition: transform 0.8s cubic-bezier(0.165, 0.84, 0.44, 1);
        }

        .btn, button, .nav-link, .trend-item {
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        }
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        .trend-item:hover {
            transform: translateX(10px);
            background: #f0f4f8;
        }
        </style>
"""

h = re.sub(r'@keyframes fadeUp \{.*?</style>', new_animations, h, flags=re.DOTALL)

# Let's fix the gap margin at the top since we removed the hero
# Add a margin-top to the main layout to give it breathing room from the ticker
h = h.replace('<div class="layout">', '<div class="layout" style="margin-top: 40px;">')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
