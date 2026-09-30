import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Add Search to Navbar
search_html = '''
                <form method="get" action="/" class="d-flex" style="margin-right: 20px; align-items: center; background: #f0f4f8; border-radius: 20px; padding: 2px 15px;">
                    <i class="fas fa-search" style="color: var(--muted); font-size: 0.9rem;"></i>
                    <input type="text" name="q" placeholder="Search news..." style="background: transparent; border: none; outline: none; padding: 6px 10px; font-size: 0.9rem; width: 200px;">
                </form>
'''

if 'name="q"' not in h:
    h = h.replace('<div class="ms-auto d-flex align-items-center flex-wrap">', '<div class="ms-auto d-flex align-items-center flex-wrap">\n' + search_html)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(h)

