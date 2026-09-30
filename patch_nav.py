import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add profile/login to navbar
auth_nav = '''
                {% if current_user.is_authenticated %}
                    <a class="nav-link" href="/profile"><i class="fas fa-user"></i>Profile</a>
                {% else %}
                    <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt"></i>Login</a>
                {% endif %}
'''
html = html.replace('<a class="nav-link" href="/ai-search"><i class="fas fa-robot"></i>AI Research</a>', '<a class="nav-link" href="/ai-search"><i class="fas fa-robot"></i>AI Research</a>' + auth_nav)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
