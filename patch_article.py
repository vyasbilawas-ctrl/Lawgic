import re

with open('templates/article.html', 'r', encoding='utf-8') as f:
    html = f.read()

share_buttons = '''
    <div style="margin: 20px 0; display: flex; gap: 10px;">
        <span style="font-weight: 600; color: var(--muted); margin-right: 10px;">Share:</span>
        <a href="https://api.whatsapp.com/send?text={{ article.title|urlencode }}%20-%20{{ request.url|urlencode }}" target="_blank" style="color: #25D366; font-size: 1.2rem;"><i class="fab fa-whatsapp"></i></a>
        <a href="https://twitter.com/intent/tweet?text={{ article.title|urlencode }}&url={{ request.url|urlencode }}" target="_blank" style="color: #1DA1F2; font-size: 1.2rem;"><i class="fab fa-twitter"></i></a>
        <a href="https://www.linkedin.com/shareArticle?mini=true&url={{ request.url|urlencode }}&title={{ article.title|urlencode }}" target="_blank" style="color: #0077b5; font-size: 1.2rem;"><i class="fab fa-linkedin"></i></a>
    </div>
'''

html = html.replace('<div class="content">', share_buttons + '\n<div class="content">')

with open('templates/article.html', 'w', encoding='utf-8') as f:
    f.write(html)
