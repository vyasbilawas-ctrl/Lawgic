import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Font Import
html = re.sub(
    r'<link href="https://fonts\.googleapis\.com/css2[^"]+" rel="stylesheet">',
    '<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700;800&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">',
    html
)

# 2. Update CSS font-families
html = html.replace("font-family: 'Inter', sans-serif;", "font-family: 'Lora', serif; font-size: 1.05rem;")
html = html.replace("font-family: 'Playfair Display', serif;", "font-family: 'Cinzel', serif;")

# 3. Update Hero Section
old_hero = '''<header class="hero">
    <div class="container-lg">
        <h1>⚖️ Legal Intelligence</h1>
        <p>Latest Indian legal news, insights & AI-powered research</p>
    </div>
</header>'''

new_hero = '''<header class="hero" style="background: linear-gradient(to bottom, #ffffff, #f5f7fa); border-bottom: 1px solid var(--line); padding: 70px 0;">
    <div class="container-lg text-center">
        <h1 style="font-size: 4rem; color: var(--primary); margin-bottom: 15px;"><i class="fas fa-balance-scale" style="color: var(--accent); margin-right: 15px;"></i>LAWGIC</h1>
        <p style="font-size: 1.4rem; color: var(--muted); font-family: 'Lora', serif; max-width: 700px; margin: 0 auto; line-height: 1.8;">India's Premier Legal Intelligence, Bare Acts & AI Research Platform</p>
    </div>
</header>'''

html = html.replace(old_hero, new_hero)

# 4. Update Brand Logo in Navbar
html = re.sub(
    r'<a class="navbar-brand brand notranslate" href="/">.*?</a>',
    '''<a class="navbar-brand brand notranslate" href="/" style="font-size: 2.2rem; letter-spacing: 1px;">
            <i class="fas fa-balance-scale" style="color: var(--accent); margin-right: 12px;"></i>LAWGIC
            <small class="notranslate" style="font-family: 'Inter', sans-serif; font-size: 0.7rem; letter-spacing: 0.2em; color: var(--muted);">Legal News & Research</small>
        </a>''',
    html,
    flags=re.DOTALL
)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
