import re

with open('templates/article.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add bookmark button
bookmark_html = '''
    <div style="margin: 20px 0;">
        {% if current_user.is_authenticated %}
            <button onclick="toggleBookmark({{ article.id }})" class="btn btn-sm btn-outline-primary"><i class="fas fa-bookmark"></i> Save Article</button>
            <script>
            function toggleBookmark(id) {
                fetch('/api/bookmark/' + id, {method: 'POST'})
                .then(r => r.json())
                .then(data => alert('Article ' + data.status + '!'));
            }
            </script>
        {% endif %}
    </div>
'''

html = html.replace('<div class="meta">', bookmark_html + '\n<div class="meta">')

with open('templates/article.html', 'w', encoding='utf-8') as f:
    f.write(html)
