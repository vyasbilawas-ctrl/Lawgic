import re
import glob

files = glob.glob('templates/*.html')

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Update fonts import
    html = re.sub(
        r'<link href="https://fonts\.googleapis\.com/css2[^"]+" rel="stylesheet">',
        '<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700;800&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">',
        html
    )
    
    # Update CSS
    html = html.replace("font-family: 'Inter', sans-serif;", "font-family: 'Lora', serif; font-size: 1.05rem;")
    html = html.replace("font-family: 'Playfair Display', serif;", "font-family: 'Cinzel', serif;")
    
    # Update Navbar Brand
    html = re.sub(
        r'<a class="navbar-brand brand notranslate" href="/">.*?</a>',
        '''<a class="navbar-brand brand notranslate" href="/" style="font-size: 2.2rem; letter-spacing: 1px;">
            <i class="fas fa-balance-scale" style="color: var(--accent); margin-right: 12px;"></i>LAWGIC
            <small class="notranslate" style="font-family: 'Inter', sans-serif; font-size: 0.7rem; letter-spacing: 0.2em; color: var(--muted); display: block; text-transform: uppercase;">Legal News & Research</small>
        </a>''',
        html,
        flags=re.DOTALL
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
